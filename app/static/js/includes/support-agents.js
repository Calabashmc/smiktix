import {tomSelectInstances} from './tom-select.js';

export async function fetchSupportAgents(teamId) {
  const supportAgentSelect = document.getElementById('support-agent');

  if(teamId && supportAgentSelect) {
     const tomSupportAgent = tomSelectInstances.get(supportAgentSelect.id);
    let options = []

    try {
      const response = await fetch(`/api/get_team_members/?team=${teamId}`);
      const data = await response.json();

      // Add new options
      for (let member of data['members']) {
        if (member[0] === '') {
          tomSupportAgent.settings.placeholder = 'Not yet assigned...'
          tomSupportAgent.inputState();
        } else {
          options.push({
            value: member[0],
            text: member[1]
          });
        }
      }
      // Refresh the select box
      tomSupportAgent.clear();
      tomSupportAgent.clearOptions();
      tomSupportAgent.addOption(options)
      tomSupportAgent.refreshItems();

    } catch (error) {
      console.log(error);
    }
  }
}
