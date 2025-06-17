import OrgChart from '../orgchart/orgchart.js';
import {getCurrentUser} from './utils.js';


class OrgChartClass {
    constructor() {
        this.DIR = '/static/images/users/'
        this.dataSource = {};

        this.ajaxURLs = {}
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

        const ajaxURLs = {
            children: '/api/orgchart/children/', parent: '/api/orgchart/parent/', siblings: (nodeData) => {
                return '/api/orgchart/siblings/' + nodeData.id;
            }, families: (nodeData) => {
                return '/api/orgchart/families/' + nodeData.id;
            }
        };

        const orgchart = new OrgChart({
            chartContainer: '#chart-container', // ajaxURL: ajaxURLs,
            data: this.dataSource,
            nodeContent: 'title',
            pan: true,
            parentNodeSymbol: null,
            toggleSiblingsResp: false,
            createNode: (node, data) => {
                if (data['avatar']) {
                    const elAvatar = document.createElement('img');
                    elAvatar.className = 'avatar';
                    elAvatar.src = `${this.DIR + data['avatar']}`;
                    node.insertBefore(elAvatar, node.firstChild);
                }

                /* onClick */
                node.addEventListener('dblclick', () => {
                    Swal.fire({
                        toast: true,
                        iconHtml: `<img src='${this.DIR + data['avatar']}' height='80px'>`,
                        title: 'Contact Details',
                        html: `<h4>${data['name']}</h4>
                                <h5>${data['title']}</h5>
                                <a href='mailto://${data['email']}'>${data['email']}</a> 
                                <br> <a href='tel://${data['phone']}'>${data['phone']}</a>`,
                        width: 450,
                    })
                })
            }
        });
    }
}

const orgChartClass = new OrgChartClass()
await orgChartClass.init()

