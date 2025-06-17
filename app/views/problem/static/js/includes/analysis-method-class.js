export class AnalysisMethodClass {
    constructor() {
        this.analysisMethod = document.querySelectorAll('input[name="analysis_method"]');
        this.fiveWhysTab = document.getElementById('five-whys-tab');
        this.genericTab = document.getElementById('generic-tab');
        this.ktTab = document.getElementById('kt-tab');
    }

    init(){
        this.setTabToMethod();
        this.setupListeners();
    }

    setupListeners(){
        this.analysisMethod.forEach(method => {
            method.addEventListener('change', (e)=>{
                if(e.target.value === 'five_whys'){
                    this.fiveWhysTab.classList.remove('disabled');
                    this.genericTab.classList.add('disabled');
                    this.ktTab.classList.add('disabled');
                    this.fiveWhysTab.click();
                } else if(e.target.value === 'generic'){
                    this.fiveWhysTab.classList.add('disabled');
                    this.genericTab.classList.remove('disabled');
                    this.ktTab.classList.add('disabled');
                    this.genericTab.click();
                } else {
                    this.fiveWhysTab.classList.add('disabled');
                    this.genericTab.classList.add('disabled');
                    this.ktTab.classList.remove('disabled');
                    this.ktTab.click();
                }
            });
        });
    }

    setTabToMethod(){
        this.analysisMethod.forEach(method => {
        if(method.checked){
            if(method.value === 'five_whys'){
                this.fiveWhysTab.classList.remove('disabled');
                this.genericTab.classList.add('disabled');
                this.ktTab.classList.add('disabled');
                this.fiveWhysTab.click();
            } else if(method.value === 'generic'){
                this.fiveWhysTab.classList.add('disabled');
                this.genericTab.classList.remove('disabled');
                this.ktTab.classList.add('disabled');
                this.genericTab.click();
            } else {
                this.fiveWhysTab.classList.add('disabled');
                this.genericTab.classList.add('disabled');
                this.ktTab.classList.remove('disabled');
                this.ktTab.click();
            }
        }
    })
    }
}