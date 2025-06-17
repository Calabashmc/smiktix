import * as echarts from '../../echarts/echarts.esm.js';

const colorList = {
    account_status: {
        'active': '#198754',
        'inactive': '#ff0000'
    },
    category: {
        'Hardware': '#c0c0c0',
        'Service': '#198754',
        'Software': '#0dcaf0',
    },
    priorities: {
        'P1': '#ff0000',
        'P2': '#ffc107',
        'P3': '#0d6efd',
        'P4': '#198754',
        'P5': 'grey'
    },
    risk: {
        'CR1': '#ff0000',
        'CR2': '#fd7e14',
        'CR3': '#0d6efd',
        'CR4': '#198754',
        'CR5': 'grey'
    },
    useful: {
        'useful': '#198754'
    },
    status: {
        'approval': '#b7410e',
        'build': '#ffc107',
        'cab': '#6610f2',
        'new': '#0d6efd',
        'in-progress': '#198754',
        'resolved': '#ffc107',
        'closed': '#ff0000',
        'plan': '#fd7e14',
        'planning': '#fd7e14',
        'implement': '#198754',
        'review': '#F4364C',
        'voting': '#ffc107',
        'adopting': '#198754',
        'archived': '#ff0000',
        'testing': '#6610f2',
        'operational': '#198754',
        'retired': '#ffc107',
        'disposed': '#ff0000',
        'internal': '#6610f2',
        'published': '#198754',
        'reviewing': '#F4364C',
        'approved': '#198754',
        'denied': '#ff0000',
        'pending': '#ffc107',
    },
    likelihood: {
        'Unlikely': '#ff0000',
        'Possible': '#0d6efd',
        'Likely': '#198754'
    },
    ticket_type: {
        'Incident': '#ffc107',
        'Request': '#198754',
    },
    change_type: {
        'Standard': '#198754',
        'Normal': '#0d6efd',
        'Urgent': '#ffc107',
        'Emergency': '#ff0000',
    },
    users: {
        'active': '#198754',
        'inactive': '#F4364C',
    },
    importance: {
        'Platinum': '#e5e4e2',
        'Gold': '#ffc107',
        'Silver': '#c0c0c0',
        'Bronze': '#cd7f32',
        'Rust': '#b7410e'
    },
    Incident: {
        'total': '#198754'
    },
    Incidents: {
        'Total': '#0dcaf0',
        'resolve-breach': '#ff0000',
        'response-breach': '#fd7e14'
    },
    Requests: {
        'Total': '#198754',
        'resolve-breach': '#ff0000',
        'response-breach': '#fd7e14'
    },
    changes: '#0d6efd',
    incidents: '#ff0000',
    problems: '#F4364C',
    requests: '#198754'
};

export class DynamicChart {
    constructor(apiUrl, chartDiv, chartType, title, filter, scope, model, ticketType, table) {
        this.apiUrl = apiUrl;
        this.chartDiv = document.getElementById(chartDiv);
        this.chartType = chartType;
        this.colorList = colorList[filter] || '#0d6efd';
        this.customTable = table;
        this.filter = filter;
        this.isDarkMode = document.body.classList.contains('bg-dark');
        this.scope = scope;
        this.ticketModel = model;
        this.ticketType = ticketType;
        this.title = title;
        this.chart = null;
    }

    get baseOptions() {
        return {
            title: {
                text: this.title,
                textStyle: {
                    fontSize: 20,
                    color: this.themeColours,
                },
            },
            tooltip: {},
            series: [],

        };
    }

    get themeColours() {
        return this.isDarkMode ? '#fff' : '#000'
    }

    initChartInstance() {
        const existing = echarts.getInstanceByDom(this.chartDiv);
        if (existing) existing.dispose();
        this.chart = echarts.init(this.chartDiv, null, {renderer: 'canvas'});
    }

    async init() {
        this.initChartInstance();
        await this.fetchDataAndRenderChart();
        this.attachChartEvent();
    }

    dispose() {
        if (this.chart) {
            this.chart.dispose();
            this.chart = null;
        }
    }

    async fetchDataAndRenderChart() {
        const apiArgs = {
            model: this.ticketModel,
            scope: this.scope,
            ticket_type: this.ticketType,
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
        };

        try {
            const response = await fetch(this.apiUrl, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(apiArgs),
            });

            if (!response.ok) throw new Error(`HTTP error ${response.status}`);
            const data = await response.json();

            const xLabels = Object.keys(data).sort();
            const options = this.getChartOptions(xLabels, data);
            const finalOptions = {...this.baseOptions, ...options};

            if (xLabels.length === 0) {
                finalOptions.graphic = {
                    elements: [{
                        type: 'image',
                        id: 'nodata',
                        left: 'center',
                        top: 'center',
                        z: 10,
                        bounding: 'raw',
                        style: {
                            image: '/static/images/shrug-stickman.png',
                            width: 100,
                            height: 100
                        },
                        silent: true,
                    }]
                };
            }

            this.setChartOptions(finalOptions);
        } catch (error) {
            console.error(`Error fetching data for ${this.title}:`, error);
            if (this.chart && !this.chart.isDisposed?.()) {
                this.chart.showLoading({text: 'Error fetching data', color: '#dc3545'});
            }
        }
    }

    getChartOptions(xLabels, data) {
        const options = {
            animation: false,
            tooltip: {},
            series: [],
        };

        const chartTypes = {
            'bar': this.getBarChartOptions,
            'dual-bar': this.getDualBarChartOptions,
            'horizontalBar': this.getHorizontalBarChartOptions,
            'pie': this.getPieChartOptions,
            'line': this.getLineChartOptions,
            'polar-endAngle': this.getPolarEndAngleOptions,
            'stacked-horizontal': this.getStackedHorizontalChartOptions,
            'pie-roseType-simple': this.getPieRoseTypeSimpleOptions,
            'radar': this.getRadarChartOptions,
        };

        const chartFunction = chartTypes[this.chartType] || this.getBarChartOptions;
        chartFunction.call(this, options, xLabels, data);

        return options;
    }

    setChartOptions(options) {
        if (this.chart && !this.chart.isDisposed?.()) {
            this.chart.setOption(options, true);
        } else {
            console.warn('Cannot set options: chart is disposed');
        }
    }

    updateChartColors(isDarkMode) {
        if (!this.chart) return;

        const textColor = isDarkMode ? '#ffffff' : '#000000';
        const backgroundColor = isDarkMode ? '#000000' : '#f1f2f3';

        const currentOptions = this.chart.getOption();

        // Update series labels
        if (currentOptions.series) {
            currentOptions.series.forEach(series => {
                // Inner "All" pie label
                if (series.name === 'All' && series.label) {
                    series.label.color = textColor;
                }
            });
        }

        // Update axis label colors safely (if present)
        const updatedXAxis = (currentOptions.xAxis || []).map(axis => ({
            ...axis,
            axisLabel: {
                ...axis.axisLabel,
                color: textColor
            }
        }));

        const updatedYAxis = (currentOptions.yAxis || []).map(axis => ({
            ...axis,
            axisLabel: {
                ...axis.axisLabel,
                color: textColor
            }
        }));

        this.chart.setOption({
            backgroundColor: backgroundColor,
            title: {
                textStyle: {
                    color: textColor
                }
            },
            legend: {
                textStyle: {
                    color: textColor
                }
            },
            xAxis: updatedXAxis,
            yAxis: updatedYAxis,
            series: currentOptions.series  // apply the patched series back
        });
    }


    handleDblClick(params) {
        if (!this.customTable) return;

        this.customTable.table.clearFilter(true);
        const inputElement = document.querySelector('input[name="filter-value"]');
        if (inputElement) inputElement.value = null;

        const onDataLoaded = () => {
            this.customTable.table.off('dataLoaded', onDataLoaded);
            Object.assign(this.customTable.apiArgs, {
                params: {
                    name: params.name,
                    model: this.ticketModel,
                    ticket_type: this.ticketType,
                    filter: this.filter,
                    status: this.status,
                },
                page: 1,
                size: 10,
                scope: this.scope,
                ticket_type: this.ticketType,
            });
            this.customTable.table.setData();
        };

        this.customTable.table.on('dataLoaded', onDataLoaded);
    }

    simulateDoubleClick(itemName) {
        this.customTable.table.off('dataLoaded');
        const chartOptions = this.chart.getOption();
        let axisData, axisType;

        if (chartOptions.xAxis && chartOptions.xAxis[0].data) {
            axisData = chartOptions.xAxis[0].data;
            axisType = 'xAxis';
        } else if (chartOptions.yAxis && chartOptions.yAxis[0].data) {
            axisData = chartOptions.yAxis[0].data;
            axisType = 'yAxis';
        } else {
            console.error('Could not find axis data.');
            return;
        }

        const itemIndex = axisData.findIndex(label => label === itemName);
        if (itemIndex !== -1) {
            this.chart.dispatchAction({
                type: 'dblclick',
                seriesIndex: 0,
                dataIndex: itemIndex
            });
            this.handleDblClick({name: itemName});
        } else {
            console.error(`Label '${itemName}' not found in ${axisType} data.`);
        }
    }

    attachChartEvent() {
        this.chart.on('dblclick', 'series', params => this.handleDblClick(params));
    };

    processedLabels(xLabels) {
        return xLabels.map(label => {
            const words = label.split(' ');
            if (words.length >= 2) {
                return words[0] + '\n' + words.slice(1).join(' ');
            }
            return label;  // <-- Fix: return label if it's a single word
        });
    }


    getBarChartOptions(options, xLabels, data) {
        options.xAxis = {
            type: 'category',
            data: this.processedLabels(xLabels),
            axisLabel: {
                rotate: 30,
                fontSize: 14,
                color: this.themeColours,
                margin: 15
            }
        };
        options.yAxis = {};
        options.legend = {show: false};
        options.series.push({
            name: 'Data',
            type: 'bar',
            data: xLabels.map(name => ({
                value: data[name],
                itemStyle: {color: this.colorList[name] || 'blue'},
                label: {show: true, position: 'inside', formatter: '{c}', fontWeight: 'bold'}
            }))
        });
    }

    getDualBarChartOptions(options, xLabels, data) {
        const firstData = data[xLabels[0]] || {};
        const valueKeys = Object.keys(firstData);

        if (valueKeys.length < 2) {
            console.warn('Not enough data keys to render dual bar chart');
            return;
        }

        const [firstKey, secondKey] = valueKeys;

        options.xAxis = {
            type: 'category',
            data: this.processedLabels(xLabels),
            axisLabel: {
                rotate: 30,
                fontSize: 14,
                color: this.themeColours
            }
        };

        options.yAxis = {type: 'value'};
        options.legend = {
            data: [this.formatLabel(firstKey), this.formatLabel(secondKey)],
            orient: 'horizontal',
            right: 10, top: 20,
            textStyle: {
                fontSize: 15,
                color: this.themeColours,
            },
        };
        options.tooltip = {
            trigger: 'axis',
            axisPointer: {type: 'shadow'}
        };

        options.series = [
            {
                name: this.formatLabel(firstKey),
                type: 'bar',
                barGap: '-40%',  // bar overlap
                barCategoryGap: '50%',  // controls overall width of bar group
                emphasis: {focus: 'series'},
                itemStyle: {color: this.colorList[firstKey] || '#0d6efd'},
                label: {show: true, position: 'inside'},
                data: xLabels.map(label => data[label]?.[firstKey] || 0)
            },
            {
                name: this.formatLabel(secondKey),
                type: 'bar',
                emphasis: {focus: 'series'},
                itemStyle: {color: this.colorList[secondKey] || '#198754'},
                label: {show: true, position: 'inside'},
                data: xLabels.map(label => data[label]?.[secondKey] || 0)
            }
        ];
    }

    formatLabel(key) {
        return key
            .replace(/_/g, ' ')
            .replace(/\b\w/g, char => char.toUpperCase());
    }

    getHorizontalBarChartOptions(options, xLabels, data) {
        options.yAxis = {
            data: this.processedLabels(xLabels),
            axisLabel: {
                fontSize: 14,
                color: this.themeColours}
        };
        options.xAxis = {};
        options.legend = {show: false};
        options.grid = {left: '30%', right: '30%'}
        options.series.push({
            name: 'Data',
            type: 'bar',
            data: xLabels.map(name => ({
                value: data[name],
                itemStyle: {color: this.colorList[name] || '#0d6efd'},
                label: {show: true, position: 'inside', formatter: '{c}', fontWeight: 'bold'}
            }))
        });
    }

    getPieChartOptions(options, statuses, data) {
        const legendData = statuses;
        const totalValue = statuses.reduce((sum, status) => sum + (data[status] || 0), 0);
        options.legend = {
            data: legendData,
            orient: 'vertical',
            right: 0,
            top: 20,
            textStyle: {
                fontSize: 12,
                color: this.themeColours,
            },
        };
        options.series.push({
            name: 'Data',
            type: 'pie',
            radius: [50, 70],
            center: ['30%', '50%'],
            itemStyle: {borderRadius: 0},
            data: statuses.map(status => ({
                name: status,
                value: data[status],
                itemStyle: {color: this.colorList[status] || 'blue'},
                label: {show: true, position: 'inside', formatter: '{c}', fontWeight: 'bold'}
            })),
        });

        options.series.push({
            name: 'All',
            type: 'pie',
            radius: [0, 20],
            center: ['30%', '50%'],
            label: {
                show: true,
                position: 'center',
                formatter: `Total\n${totalValue}`,
                fontSize: 16,
                fontWeight: 'bold',
                color: this.isDarkMode ? '#ffffff' : '#000000',
            },
            data: [{value: totalValue, name: 'All'}],
            itemStyle: {color: 'transparent'}
        });
    }

    getLineChartOptions(options, xLabels, data) {
        options.xAxis = {
            type: 'category',
            boundaryGap: false,
            data: this.processedLabels(xLabels),
            axisLabel: {rotate: 60}
        };
        options.yAxis = {type: 'value', name: 'Count'};
        if (data['tickets'] && Object.keys(data['tickets']).length > 0) {
            options.series.push({
                name: 'Volume',
                type: 'line',
                areaStyle: {},
                data: Object.values(data['tickets']),
            });
        }
    }

    getPolarEndAngleOptions(options, xLabels, data) {
        const categories = Object.keys(data[xLabels[0]]);
        options.angleAxis = [
            {
                type: 'category',
                polarIndex: 0,
                startAngle: 85,
                endAngle: -5,
                data: categories,
                axisLabel: {
                    fontSize: 14,
                    color: this.themeColours
                }
            },
            {
                type: 'category',
                polarIndex: 1,
                startAngle: -95,
                endAngle: -190,
                data: categories,
                axisLabel: {
                    fontSize: 14,
                    color: this.themeColours
                }
            }
        ];

        options.radiusAxis = [
            {polarIndex: 0, axisLabel: {color: this.themeColours}},
            {polarIndex: 1, axisLabel: {color: this.themeColours}}
        ];

        options.polar = [{}, {}];

        const seriesData1 = categories.map(category => ({
            value: data[xLabels[0]][category],
            itemStyle: {color: colorList[xLabels[0]][category]},
            label: {
                show: true,
                position: 'middle',
                formatter: '{c}',
                fontWeight: 'bold',
                color: this.themeColours
            }
        }));
        const seriesData2 = categories.map(category => ({
            value: data[xLabels[1]][category],
            itemStyle: {color: colorList[xLabels[1]][category]},
            label: {
                show: true,
                position: 'middle',
                formatter: '{c}',
                fontWeight: 'bold',
                color: this.themeColours
            }
        }));

        options.series = [
            {
                name: xLabels[0],
                type: 'bar',
                coordinateSystem: 'polar',
                polarIndex: 0,
                itemStyle: {color: colorList[xLabels[0]]['Total']},
                data: seriesData1,
            },
            {
                name: xLabels[1],
                type: 'bar',
                coordinateSystem: 'polar',
                polarIndex: 1,
                itemStyle: {color: colorList[xLabels[1]]['Total']},
                data: seriesData2,
            }
        ];

        options.legend = {
            show: true,
            orient: 'vertical',
            left: 'right',
            textStyle: {color: this.themeColours},
            data: xLabels
        };
    }

    getStackedHorizontalChartOptions(options, xLabels, data) {
        const categories = Object.keys(data[xLabels[0]]);

        options.grid = {
            left: '3%',
            right: '4%',
            bottom: '3%',
            containLabel: true
        }

        options.xAxis = {type: 'value'};
        options.yAxis = {
            type: 'category',
            data: xLabels,
            axisLabel: {
                formatter: '{value}  ',
                fontSize: 14,
                color: this.themeColours,
                lineHeight: 20,
                margin: 20,
            }
        };

        options.tooltip = {
            trigger: 'axis',
            axisPointer: {type: 'shadow'},
        };

        options.legend = {
            data: categories,
            textStyle: {color: this.themeColours}
        };

        categories.forEach(category => {
            const seriesData = xLabels.map(label => data[label][category] || 0);

            options.series.push({
                name: category,
                type: 'bar',
                stack: 'total',
                emphasis: {focus: 'series'},
                label: {
                    show: true,
                    fontSize: 14,
                    formatter: '{c}',
                },
                data: seriesData,
                itemStyle: {
                    color: colorList[category] || this.getRandomColor(category)
                }
            });
        });
    }

    getPieRoseTypeSimpleOptions(options, xLabels, data) {
        const totalValue = xLabels.reduce((sum, label) => sum + (data[label] || 0), 0);

        options.tooltip = {
            trigger: 'item',
            formatter: '{a} <br/>{b}: {c} ({d}%)'
        };

        options.legend = {
            orient: 'vertical',
            right: 10,
            top: 'center',
            data: xLabels,
            textStyle: {color: this.themeColours}
        };

        options.series= [{
            name: this.title,
            type: 'pie',
            radius: [30, '60%'],
            center: ['40%', '50%'],
            roseType: 'area',
            itemStyle: {borderRadius: 5},
            label: {formatter: '{b}: {c} ({d}%)'},
            data: xLabels.map(name => ({
                value: data[name],
                name: name,
                itemStyle: {
                    color: this.colorList[name] || this.getRandomColor(name)
                }
            }))
        }];

        options.graphic = [{
            type: 'text',
            left: '40%',
            top: '50%',
            style: {
                text: `Total\n${totalValue}`,
                fontSize: 16,
                fontWeight: 'bold',
                textAlign: 'center',
                fill: this.isDarkMode ? '#fff' : '#333'
            }
        }];
    }

    getRadarChartOptions(options, xLabels, data) {
        const categories = Object.keys(data[xLabels[0]]);
        options.xAxis = undefined;
        options.yAxis = undefined;

        const allValues = xLabels.flatMap(team => Object.values(data[team]));
        const maxValue = Math.max(...allValues);

        const indicators = xLabels.map(team => ({
            name: team,
            max: maxValue
        }));

        options.radar = {
            indicator: indicators,
            center: ['25%', '50%'],
            radius: 120,
            startAngle: 90,
            splitNumber: 4,
        };

        options.tooltip = {trigger: 'item'};

        const seriesData = categories.map(category => ({
            name: category.charAt(0).toUpperCase() + category.slice(1),
            value: xLabels.map(team => data[team][category] || 0),
        }));

        options.series = seriesData.map(series => ({
            name: series.name,
            type: 'radar',
            data: [{
                value: series.value,
                name: series.name,
                areaStyle: {opacity: 0.3}
            }]
        }));

        options.legend = {
            orient: 'vertical',
            right: 10,
            top: 'center',
            data: seriesData.map(series => series.name),
            textStyle: {color: this.themeColours}
        };
    }

    getRandomColor(str) {
        let hash = 0;
        for (let i = 0; i < str.length; i++) {
            hash = str.charCodeAt(i) + ((hash << 5) - hash);
        }

        const r = (hash & 0xFF0000) >> 16;
        const g = (hash & 0x00FF00) >> 8;
        const b = hash & 0x0000FF;

        return `rgb(${r}, ${g}, ${b})`;
    }
}
