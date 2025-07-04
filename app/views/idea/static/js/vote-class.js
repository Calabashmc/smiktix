import {getCurrentUser} from '../../../../static/js/includes/utils.js';
import {showSwal} from '../../../../static/js/includes/form-classes/form-utils.js';

export class VoteClass {
    constructor() {
        this.likelihood = document.getElementById('likelihood');
        this.requester = document.getElementById('requested-by');
        this.ticketNumber = document.getElementById('ticket-number');
        this.voteButtons = document.querySelectorAll('input[name="idea-rating"]');
        this.voteCount = document.getElementById('vote-count');
        this.voteScore = document.getElementById('vote-score');

    }

    init() {
        this.voteButtonListener();
    }

    voteButtonListener() {
        // const currentScore = Number(this.voteScore.value);
        // let clickScore = 0;
        // const currentCount =

        this.voteButtons.forEach((voteBtn) => {
            voteBtn.addEventListener('click', async () => {
                let apiArgs = {
                    'ticket-number': this.ticketNumber.value,
                    'vote-score': voteBtn.value,
                }

                let response = await fetch('/api/idea_vote/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(apiArgs),
                })
                let data = await response.json()
                if (data) {
                    if (data['status']) {
                        await showSwal(
                            'Not yet set for Voting!',
                            'The Idea Status needs to be <mark>Voting</mark> before voting can commence ',
                            'success'
                        );

                    } else if (data['my-idea']) {
                        await showSwal("You can't vote on your own Idea!, Someone else might though with some encouragement " +
                            '<svg width=\'40px\' height=\'40px\' viewBox=\'0 0 1024 1024\' class=\'icon\' version=\'1.1\' xmlns=\'http://www.w3.org/2000/svg\' fill=\'#000000\'><g id=\'SVGRepo_bgCarrier\' stroke-width=\'0\'></g><g id=\'SVGRepo_tracerCarrier\' stroke-linecap=\'round\' stroke-linejoin=\'round\'></g><g id=\'SVGRepo_iconCarrier\'><path d=\'M512 213.333333m-85.333333 0a85.333333 85.333333 0 1 0 170.666666 0 85.333333 85.333333 0 1 0-170.666666 0Z\' fill=\'#F44336\'></path><path d=\'M874.666667 554.666667c0-94.272-162.368-170.666667-362.666667-170.666667S149.333333 460.394667 149.333333 554.666667c0 22.634667 10.688 33.088 29.546667 36.010666C188.032 630.058667 329.685333 661.333333 512 661.333333c180.992 0 321.344-30.826667 332.266667-69.781333C863.936 590.613333 874.666667 580.629333 874.666667 554.666667z\' fill=\'#795548\'></path><path d=\'M746.666667 874.666667H277.333333L170.666667 576l42.666666 42.666667 42.666667-42.666667 42.666667 42.666667 42.666666-42.666667 42.666667 42.666667 42.666667-42.666667 42.666666 42.666667 42.666667-42.666667 42.666667 42.666667 42.666666-42.666667 42.666667 42.666667 42.666667-42.666667 42.666666 42.666667 42.666667-42.666667 42.666667 42.666667 42.666666-42.666667z\' fill=\'#FF80AB\'></path><path d=\'M874.666667 554.666667a82.986667 82.986667 0 0 0-3.776-23.317334l-18.453334-14.890666L810.666667 558.336l-12.501334-12.501333L768 515.669333l-30.165333 30.165334-12.501334 12.501333-12.501333-12.501333L682.666667 515.669333l-30.165334 30.165334-12.501333 12.501333-12.501333-12.501333L597.333333 515.669333l-30.165333 30.165334-12.501333 12.501333-12.501334-12.501333L512 515.669333l-30.165333 30.165334-12.501334 12.501333-12.501333-12.501333L426.666667 515.669333l-30.165334 30.165334-12.501333 12.501333-12.501333-12.501333L341.333333 515.669333l-30.165333 30.165334-12.501333 12.501333-12.501334-12.501333L256 515.669333l-30.165333 30.165334-12.501334 12.501333-42.666666-40.106667-19.562667 19.904A82.410667 82.410667 0 0 0 149.333333 554.666667c0 20.842667 9.386667 31.018667 25.557334 34.858666L170.666667 576l42.666666 42.666667 42.666667-42.666667 42.666667 42.666667 42.666666-42.666667 42.666667 42.666667 42.666667-42.666667 42.666666 42.666667 42.666667-42.666667 42.666667 42.666667 42.666666-42.666667 42.666667 42.666667 42.666667-42.666667 42.666666 42.666667 42.666667-42.666667 42.666667 42.666667 42.666666-42.666667-4.714666 15.04C865.450667 588.842667 874.666667 578.581333 874.666667 554.666667z\' fill=\'#5D4037\'></path><path d=\'M426.666667 576l-42.666667 42.666667 45.354667 256h27.541333zM341.333333 576l-42.666666 42.666667 64 256h32.021333zM256 576l-42.666667 42.666667 85.333334 256h31.104zM597.077333 576L554.666667 618.666667l-13.098667 256h25.536zM682.410667 576L640 618.666667l-39.104 256h27.541333zM768 576l-42.666667 42.666667-62.229333 256 30.229333 0.896zM512 576l-42.666667 42.666667 16.021334 256H512zM810.666667 618.666667l42.666666-42.666667-106.666666 298.666667h-25.770667z\' fill=\'#F8BBD0\'></path><path d=\'M744.810667 377.429333c0 96.426667-104.213333 36.757333-232.810667 36.757334s-232.810667 59.669333-232.810667-36.757334C279.189333 280.981333 383.402667 234.666667 512 234.666667s232.810667 46.314667 232.810667 142.762666z\' fill=\'#FFE0B2\'></path></g></svg>',
                            'error')
                    } else if (data['already-voted']) {
                        await showSwal('Already Voted', 'You have already voted for this Idea!', 'error');
                    } else {
                        this.voteScore.value = data['score'];
                        this.voteCount.value = data['count'];
                        this.likelihood.value = data['likelihood']
                    }
                }
            })
        })
    }

    async checkIfOwn() {
        const currentUser = await getCurrentUser();

        return currentUser.user_id === this.requester.value;
    }
}


