import '../vis-network/vis-network.js'

export class VisNetworkClass {
    constructor() {
        this.DIR = '/static/images/vis-network/';
        this.CIid = null; // initialise for CI ID
        this.modal = document.getElementById('network-view-modal');
        this.modalNetworkContainer = document.getElementById('modal-network-container');
        if (this.modal) {
            this.networkViewModal = new bootstrap.Modal(this.modal);
        } else {
            this.networkViewModal = null;
        }
        this.network = null;
        this.networkContainer = document.getElementById('network-container');
        this.nodes = new vis.DataSet();
        this.edges = new vis.DataSet();
    }

    async getVisNetworkIcon(ticket_number) {
        const response = await fetch(`/api/get_vis_network_icon/?ticket_number=${ticket_number}`);
        const data = await response.json();
        return data['icon'];
    }

    destroyNetwork() {
        if (this.network !== null) {
            this.nodes.clear();
            this.edges.clear();
            this.network.destroy();
            this.network = null;
        }
    }

    async popOutNetwork() {
        this.networkViewModal.show();
        setTimeout(() => {
            this.drawNetwork(this.modalNetworkContainer, this.CIid);
        }, 200);  // delay to allow time for the container to be created before drawing network
    }

    async popInNetwork() {
        this.networkViewModal.hide();
        await this.drawNetwork(this.networkContainer, this.CIid);
    }

    async drawNetwork(container, id = null, depth = 2) {
        this.destroyNetwork()
        this.CIid = id
        let response;

        if (this.CIid) {
            response = await fetch(`/api/network-data/?id=${this.CIid}&depth=${depth}`)
        } else {
            response = await fetch(`/api/network-data/?depth=${depth}`)
        }

        const data = await response.json();

        // Distinguish the main node
        data.nodes = data.nodes.map(node => {
            if (node.id === Number(this.CIid)) {
                return {
                    ...node,
                    shape: 'circularImage',
                    font: {size: 22, color: 'black',}, // Optional, adjust font for visibility
                    borderWidth: 5, // Optional, add emphasis to the border
                    color: {background: 'red', border: 'red'},
                };
            }

            return node;
        });

        this.nodes.clear();
        this.edges.clear();

        this.nodes.add(data.nodes);
        this.edges.add(data.edges);


        const networkData = {
            nodes: this.nodes,
            edges: this.edges
        };

        const options = {
            autoResize: true,
            height: '100%',
            width: '100%',
            layout: {
                improvedLayout: true,
                randomSeed: 2,
                hierarchical: {
                    enabled: false, // Enable if you want hierarchical layout
                },
            },
            nodes: {
                font: {
                    size: 18,
                    color: 'black'
                },
                borderWidth: 1,
                borderWidthSelected: 3,
                shadow: true,
            },
            edges: {
                width: 2,
                shadow: false,
            },
            physics: {
                enabled: false,
                solver: 'barnesHut', // or 'forceAtlas2Based'
                barnesHut: {
                    gravitationalConstant: -6000, // More negative to increase spacing
                    centralGravity: 0.01, // Lower value to reduce central gravity influence
                    springLength: 400, // Increase for more distance between nodes
                    springConstant: 0.2,
                },
                stabilization: {
                    iterations: 2000, // Increase to give more time for stabilization
                    updateInterval: 25, // Adjust if needed
                },
            },
        };

        this.network = new vis.Network(container, networkData, options);
        // Ensure the network fits within the view once stabilization is done
        this.network.once('stabilizationIterationsDone', () => {
            this.network.fit({
                animation: {
                    duration: 1000,
                    easingFunction: 'easeInOutQuad'
                },
                offset: {x: 0, y: 0} // Center the network in the container
            });
            this.network.redraw(); // Redraw the network to ensure it fits
        });

        this.network.once('stabilized', () => {
            this.network.fit({
                animation: {
                    duration: 1000,
                    easingFunction: 'easeInOutQuad'
                },
                offset: {x: 0, y: 0} // Center the network in the container
            });
            this.network.redraw(); // Redraw the network to ensure it fits
        });

        let lastPosition = null;
        const max_zoom = 2;
        const min_zoom = 0.5;

        this.network.on('zoom', (params) => {
            if (params.scale < min_zoom || params.scale > max_zoom) { // adjust this value according to your requirement
                this.network.moveTo({
                    position: lastPosition, // use the last position before zoom limit
                    scale: params.scale > max_zoom ? max_zoom : min_zoom // this scale prevents zooming out beyond the desired limit
                });
            } else {
                // store the current position as the last position before zoom limit
                lastPosition = this.network.getViewPosition();
            }
        });

        // Log click events
        this.network.on('click', (params) => {
            if (params.edges.length > 0) {
                const edgeId = params.edges[0];
                const edge = this.edges.get(edgeId);

                // Highlight the edge and nodes
                this.edges.update([
                        {
                            id: edgeId,
                            color: {color: 'green'},
                        }
                    ]
                );
                this.nodes.update([
                    {id: edge.from, color: {background: 'blue'}, borderWidth: 5,},
                    {id: edge.to, color: {background: 'green'}}
                ]);
            } else {
                console.log('Clicked node:', params.nodes);
            }
        })

        this.network.on('doubleClick', async (params) => {
            // Check if an item (node or edge) was clicked
            if (params.nodes.length > 0) {
                const nodeId = params.nodes[0];
                const nodeDetails = this.nodes.get(nodeId);

                if (nodeId === Number(this.CIid)) {
                    return
                }

                if (nodeDetails) {
                    const response = await fetch(`/api/get_ci_ticket_number/?id=${nodeDetails.id}`);
                    const data = await response.json();
                    if (response.ok && !data['error']) {
                        const url = data['url'];
                        window.open(url, '_blank');
                    }

                }
            }
        });
    }
}

export const visNetworkClass = new VisNetworkClass();