import * as echarts from '../echarts/echarts.esm.js';
import { getCurrentUser } from './utils.js';

class OrgChartClass {
    constructor() {
        this.DIR = '/static/images/users/'
        this.dataSource = {};
        this.chart = null;
        this.chartContainer = null;
        console.log(this.DIR)
    }

    async init() {
        const userDetails = await getCurrentUser()
        const userID = userDetails['user_id']
        await this.getData(userID);
    }

    async getData(id) {
        const response = await fetch(`/api/get-orgchart-data/?id=${id}`);
        this.dataSource = await response.json()
        this.drawOrgChart();
    }

    drawOrgChart() {
        // Initialize ECharts instance
        this.chartContainer = document.getElementById('chart-container');
        this.chart = echarts.init(this.chartContainer);
        console.log(this.chart)

        // Transform data to ECharts tree format
        const treeData = this.transformDataToTree(this.dataSource);

        const option = {
            tooltip: {
                trigger: 'item',
                triggerOn: 'mousemove',
                formatter: (params) => {
                    const data = params.data;
                    return `
                        <div style="text-align: center;">
                            ${data.avatar ? `<img src="${this.DIR + data.avatar}" style="width: 60px; height: 60px; border-radius: 50%; margin-bottom: 8px;" /><br/>` : ''}
                            <strong>${data.name || ''}</strong><br/>
                            <span style="color: #666;">${data.title || ''}</span><br/>
                            ${data.email ? `<a href="mailto:${data.email}">${data.email}</a><br/>` : ''}
                            ${data.phone ? `<a href="tel:${data.phone}">${data.phone}</a>` : ''}
                        </div>
                    `;
                }
            },
            series: [
                {
                    type: 'tree',
                    data: treeData,
                    top: '5%',
                    left: '7%',
                    bottom: '5%',
                    right: '20%',
                    symbolSize: [120, 80],
                    symbol: 'rect',
                    orient: 'TB', // Top to Bottom
                    expandAndCollapse: true,
                    animationDuration: 550,
                    animationDurationUpdate: 750,
                    lineStyle: {
                        color: '#ccc',
                        width: 2,
                        curveness: 0.5
                    },
                    label: {
                        show: true,
                        position: 'inside',
                        verticalAlign: 'middle',
                        align: 'center',
                        fontSize: 12,
                        rich: {
                            name: {
                                fontSize: 14,
                                fontWeight: 'bold',
                                color: '#333',
                                padding: [0, 0, 2, 0]
                            },
                            title: {
                                fontSize: 11,
                                color: '#666',
                                padding: [2, 0, 0, 0]
                            }
                        },
                        formatter: (params) => {
                            const data = params.data;
                            return `{name|${data.name || ''}}\n{title|${data.title || ''}}`;
                        },
                        backgroundColor: 'rgba(255, 255, 255, 0.9)',
                        borderColor: '#ccc',
                        borderWidth: 1,
                        borderRadius: 8,
                        padding: [8, 12],
                        shadowColor: 'rgba(0, 0, 0, 0.1)',
                        shadowBlur: 4,
                        shadowOffsetY: 2
                    },
                    leaves: {
                        label: {
                            position: 'inside',
                            verticalAlign: 'middle',
                            align: 'center'
                        }
                    },
                    emphasis: {
                        focus: 'descendant',
                        lineStyle: {
                            color: '#4CAF50',
                            width: 3
                        },
                        label: {
                            backgroundColor: 'rgba(76, 175, 80, 0.1)',
                            borderColor: '#4CAF50'
                        }
                    }
                }
            ],
            // Enable toolbox for zoom and pan
            toolbox: {
                show: true,
                feature: {
                    restore: { show: true, title: 'Reset' },
                    saveAsImage: { show: true, title: 'Save as Image' }
                }
            },
            // Enable data zoom for panning
            dataZoom: [
                {
                    type: 'inside',
                    xAxisIndex: [0],
                    filterMode: 'none'
                },
                {
                    type: 'inside',
                    yAxisIndex: [0],
                    filterMode: 'none'
                }
            ]
        };

        // Set the option and render
        this.chart.setOption(option);

        // Add double-click event handler
        this.chart.on('dblclick', (params) => {
            if (params.data) {
                this.handleDoubleClick(params.data);
            }
        });

        // Handle window resize
        window.addEventListener('resize', () => {
            if (this.chart) {
                this.chart.resize();
            }
        });

        // Enable pan and zoom
        this.enablePanAndZoom();
    }

    enablePanAndZoom() {
        // ECharts tree charts support pan and zoom through dataZoom
        // This is already configured in the option above

        // You can also add custom pan behavior if needed
        let isDragging = false;
        let startPoint = null;

        this.chartContainer.addEventListener('mousedown', (e) => {
            isDragging = true;
            startPoint = { x: e.clientX, y: e.clientY };
        });

        this.chartContainer.addEventListener('mousemove', (e) => {
            if (isDragging && startPoint) {
                // Custom pan logic could go here if needed
                // ECharts handles this automatically with dataZoom
            }
        });

        this.chartContainer.addEventListener('mouseup', () => {
            isDragging = false;
            startPoint = null;
        });
    }

    handleDoubleClick(data) {
        Swal.fire({
            toast: true,
            iconHtml: data.avatar ? `<img src='${this.DIR + data.avatar}' height='80px' style='border-radius: 50%;'>` : '',
            title: 'Contact Details',
            html: `<h4>${data.name}</h4>
                    <h5>${data.title}</h5>
                    ${data.email ? `<a href='mailto://${data.email}'>${data.email}</a><br/>` : ''}
                    ${data.phone ? `<a href='tel://${data.phone}'>${data.phone}</a>` : ''}`,
            width: 450,
        });
    }

    transformDataToTree(data) {
        // Transform your data structure to ECharts tree format
        // ECharts expects: { name, value, children: [] }

        if (Array.isArray(data)) {
            return this.arrayToTree(data);
        } else {
            return [this.formatTreeNode(data)];
        }
    }

    arrayToTree(flatArray) {
        // Convert flat array to hierarchical tree structure
        const map = {};
        const roots = [];

        // Create map of all nodes
        flatArray.forEach(item => {
            map[item.id] = this.formatTreeNode(item);
        });

        // Build hierarchy
        flatArray.forEach(item => {
            const node = map[item.id];
            if (item.parentId && map[item.parentId]) {
                if (!map[item.parentId].children) {
                    map[item.parentId].children = [];
                }
                map[item.parentId].children.push(node);
            } else {
                roots.push(node);
            }
        });

        return roots;
    }

    formatTreeNode(data) {
        // Format single node for ECharts tree
        const node = {
            name: data.name || data.title || 'Unknown',
            value: data.id,
            // Store all original data for access in events
            ...data,
            collapsed: false
        };

        if (data.children && Array.isArray(data.children)) {
            node.children = data.children.map(child => this.formatTreeNode(child));
        }

        return node;
    }

    // Additional utility methods
    updateChart(newData) {
        if (this.chart) {
            const treeData = this.transformDataToTree(newData);
            this.chart.setOption({
                series: [{
                    data: treeData
                }]
            });
        }
    }

    // Expand all nodes
    expandAll() {
        if (this.chart) {
            // Get current option and modify expand state
            const option = this.chart.getOption();
            this.expandAllNodes(option.series[0].data);
            this.chart.setOption(option);
        }
    }

    // Collapse all nodes
    collapseAll() {
        if (this.chart) {
            const option = this.chart.getOption();
            this.collapseAllNodes(option.series[0].data);
            this.chart.setOption(option);
        }
    }

    expandAllNodes(nodes) {
        if (Array.isArray(nodes)) {
            nodes.forEach(node => {
                if (node.children) {
                    node.collapsed = false;
                    this.expandAllNodes(node.children);
                }
            });
        }
    }

    collapseAllNodes(nodes) {
        if (Array.isArray(nodes)) {
            nodes.forEach(node => {
                if (node.children) {
                    node.collapsed = true;
                    this.collapseAllNodes(node.children);
                }
            });
        }
    }

    // Cleanup method
    dispose() {
        if (this.chart) {
            this.chart.dispose();
            this.chart = null;
        }
        window.removeEventListener('resize', this.handleResize);
    }
}

const orgChartClass = new OrgChartClass()
await orgChartClass.init()