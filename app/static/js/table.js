/* global Swal */
import {TabulatorFull as Tabulator} from './tabulator/tabulator_esm.js';
import './xlsx/xlsx.full.min.js'
import {showSwal} from './includes/form-classes/form-utils.js';

// delete column used by various tables
export const deleteColumn = {
    title: 'Del',
    headerHozAlign: 'center',
    formatter: function () {
        return "<i class='bi bi-trash3 text-danger'></i>";
    },
    width: 100,
    hozAlign: 'center',
    cellClick: async function (e, cell) {
        const response = await showSwal('Are you sure?', "You won't be able to revert this", 'question');
        if (response.isConfirmed) {
            const row = cell.getRow();
            row.delete();
        }
    },
}

export const unlinkColumn = {
    title: 'Unlink',
    headerHozAlign: 'center',
    formatter: function () {
        return "<i class='h5 las la-unlink text-danger'></i>";
    },
    width: 100,
    hozAlign: 'center',
    cellClick: async function (e, cell) {
        const response = await showSwal('Are you sure?', "You won't be able to revert this", 'question');
        if (response.isConfirmed) {
            const row = cell.getRow();
            row.delete();
        }
    },
}

export class CustomTabulator {
    constructor(url, selector, args, columns, paginate = true, filterInfoElement = 'filter-info', groupBy = null) {
        if (args) {
            this.apiArgs = args;
        } else {
            this.apiArgs = {};
        }

        this.columns = columns;
        this.filterInfoElement = document.getElementById(filterInfoElement);
        this.groupBy = groupBy;
        this.table = null;
        this.hidden = [];
        this.selector = selector;
        this.url = url;
        this.paginate = paginate;


        this.init();
    }

    init() {
        this.createTable();
    }


    createTable() {
        // CustomTabulator -> constructor(url, selector, hiddenSelector, args, columns)
        this.table = new Tabulator(this.selector, {
            // persistence: true,
            layout: 'fitColumns',
            responsiveLayout:true,
            filterMode: 'remote',
            groupBy: this.groupBy,
            pagination: this.paginate,
            paginationSize: 10,
            paginationMode: 'remote',
            paginationSizeSelector: [10, 20, 50, 100],
            paginationCounter: 'rows',
            ajaxURL: this.url,
            ajaxConfig: 'POST',
            ajaxParams: this.apiArgs,
            ajaxContentType: 'json',
            ajaxResponse: (url, params, response) => {
                this.updateFilterInfo(response['filter_description']);
                if (this.paginate) {
                    return {
                        last_page: response.last_page,
                        last_row: response.last_row,
                        data: response.data
                    };
                } else {
                    return response.data; // Return only the data array when pagination is disabled
                }
            },
            placeholder: 'No Data Set',
            columns: this.bindCustomFormatters(this.columns),
            downloadRowRange: 'active',
            selectableRows: 1,
        });

    }

    // Method to update the filter info
    updateFilterInfo(filterDescription) {
        if (this.filterInfoElement && filterDescription !== 'None') {
            this.filterInfoElement.textContent = `Filter: ${filterDescription || "None"}`;
        }
    }

    // called from the various classes displaying tables set the action for double-clicked table row.
    setRowDblClickEventHandler(handler) {
        if (handler && typeof handler === 'function') {
            this.rowDblClickHandler = handler;
            this.bindRowDblClickEvent();
        } else {
            console.error('Invalid event handler provided.');
        }
    }

    // Method to bind row double click event internally
    bindRowDblClickEvent() {
        if (this.table) {
            this.table.on('rowDblClick', (e, row) => {
                if (this.rowDblClickHandler) {
                    this.rowDblClickHandler(e, row);
                }
            });
        }
    }

    bindCustomFormatters(columns) {
        return columns.map(column => {
            if (column.formatter === 'custom') {
                column.formatter = this.customFormatter;
            }
            return column;
        });
    }

    customFormatter = (cell) => {
    const data = cell.getRow().getData();
    const isResponseBreach = data['sla_response_breach'];
    const isResolveBreach = data['sla_resolve_breach'];
    let iconHTML = '';

    if (!isResponseBreach && !isResolveBreach) {
        iconHTML = '<i class="bi bi-emoji-smile-fill text-success h4"></i>';
    } else if (isResponseBreach && !isResolveBreach) {
        iconHTML = '<i class="bi bi-emoji-neutral-fill text-warning h4\"></i>';
    } else if (isResponseBreach && isResolveBreach) {
        iconHTML = '<i class="bi bi-emoji-tear-fill text-danger h4"></i>';
    }

    return iconHTML;
};


    numberOfRows() {
        return new Promise((resolve) => {
            this.table.on('dataLoaded', (data) => {
                resolve(data.length);
            });
        });
    }


    downloadDialog(extension) {
        Swal.fire({
            width: 350,
            title: 'Download File?',
            text: 'Enter filename below to download the file.',
            icon: 'info',
            html: `<div class="input-group">
                      <input id="filename" type="text" class="form-control">
                      <span class="input-group-text">${extension}</span>
                   </div>`,
            showCancelButton: true,
            confirmButtonColor: '#3085d6',
            cancelButtonColor: '#d33',
            confirmButtonText: 'Download',
            focusConfirm: false,
            preConfirm: () => {
                const filename = document.getElementById('filename').value;
                if (!filename) {
                    Swal.showValidationMessage('Please enter a filename');
                }
                return `${filename}.${extension}`;
            }
        }).then((result) => {
            if (result.isConfirmed) {
                this.table.download(extension, result.value);
            }
        });
    }

    getTableInstance() {
        return this.table;
    }
}

