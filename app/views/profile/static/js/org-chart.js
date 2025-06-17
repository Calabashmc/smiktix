import '/static/js/vis-network/vis-network.js'
import {getCurrentUser} from '/static/js/includes/utils.js';

class OrgChart {
    constructor() {
        this.DIR = '/static/images/users/';
        this.network = null;
        this.networkContainer = document.querySelector('#network-container');
        this.networkEdges = [];
        this.networkNodes = [];
    }

    async mapOrgChart(id, value) {
        let apiArgs = {
            'id': id,
        }

        const response = await fetch(`/api/get_org_chart/?id=${id}`);
        const data = await response.json();

        if (data) {
            await this.populateNodes(data, id, value, this.networkContainer)
        }
    }

    async populateNodes(data, id, value, container) {
        const selectedUser = {id: id, label: value, image: this.DIR + data['photo'], shape: 'image',}

        const selectedUserExists = this.networkNodes.some(node => node.id === selectedUser.id);
        if (!selectedUserExists) {
            this.networkNodes.push(selectedUser)
        }

        await this.addNode(data['manager'], id, 'Reports to')

        await this.addNode(data['subordinates'], id, 'Team');

        await this.drawOrgChart(container)
    }

    async addNode(data, id, direction) {
        let newEdge;

        for (const [key, value] of Object.entries(data)) {
            const response = await fetch(`/api/people/get_requester_details/?id=${key}`)
            const data = await response.json()
            const photo = data['photo'];
            const newUser = {id: key, label: value, image: this.DIR + photo, shape: 'image'};

            // Check if an CI with the same id already exists in the array
            const userExists = this.networkNodes.some(node => node.id === newUser.id);

            if (!userExists) {
                this.networkNodes.push(newUser);
            }
            if (direction === 'Reports to') {
                newEdge = {
                    from: key, to: id, color: {color: 'blue', highlight: 'green'}, arrows: 'from',
                    width: 3,
                    length: 300,
                    label: direction,
                }
            } else {
                newEdge = {
                    from: id, to: key, color: {color: 'orange', highlight: 'yellow'}, arrows: 'from',
                    width: 3,
                    length: 200,

                }
            }

            const edgeUpstreamExists = this.networkEdges.some(edge => edge.to === newEdge.to)
            const edgeDownstreamExists = this.networkEdges.some(edge => edge.from === newEdge.to)

            if (!edgeUpstreamExists && !edgeDownstreamExists) {
                this.networkEdges.push(newEdge)
            }
        }
    }

    destroyNetwork() {
        if (this.network !== null) {
            this.network.destroy();
            this.network = null;
        }
    }

    async drawOrgChart(drawDiv) {
        this.destroyNetwork();
        let options = {
            autoResize: true,
            height: '100%',
            width: '100%',
            physics: {
                enabled: true,
            },
            layout: {
                hierarchical: {
                    direction: 'UD',
                    sortMethod: 'directed',
                    nodeSpacing: 150,
                    levelSeparation: 200,
                },
            },
            nodes: {
                font: {
                    size: 14,
                    color: 'black',
                },
                borderWidth: 2,
                shadow: true,
           },
            edges: {
                width: 2,
                shadow: true,
            },
        };

        const nodes = new vis.DataSet(this.networkNodes);
        const edges = new vis.DataSet(this.networkEdges);

        const data = {
            nodes: nodes,
            edges: edges
        };

        this.network = new vis.Network(drawDiv, data, options);

        this.network.on('click', function (params) {
            // Check if an item (node or edge) was clicked
        });
    }
}

const orgChartClass = new OrgChart();
const user_details = await getCurrentUser();
await orgChartClass.mapOrgChart(user_details['user_id'], user_details['user_name'], user_details['manager_id']);