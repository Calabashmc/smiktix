// import {initaliseTomSelectFields} from '/static/js/includes/tom-select.js';
//
// async function initiateTomSelect() {
//     await initaliseTomSelectFields();
// }

export async function cmdbCategorySelectListener() {
    const cmdbCategorySelect = document.getElementById('cmdb-category');
    const tomCategory = cmdbCategorySelect.tomselect
    const options = [];
    try {
        let response = await fetch('/api/get_cmdb_categories/')
        let data = await response.json()
        for (let category of data.categories) {
            options.push(
                {
                    value: category[0],
                    text: category[1]
                }
            );
        }

        tomCategory.clear();
        tomCategory.clearOptions();
        tomCategory.addOption(options);
        tomCategory.refreshItems();
        tomCategory.addItem(0); //select the first item as default. In this case (0, 'All CMDB Categories)

    } catch (error) {
        console.log(error);
    }
}
await initiateTomSelect()
// await cmdbCategorySelectListener()