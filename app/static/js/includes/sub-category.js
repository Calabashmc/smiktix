import {tomSelectInstances} from './tom-select.js';

export async function getSubCategories(category) {
    const subcategorySelectId = 'subcategory-id';
    const tomSubCategory = tomSelectInstances.get(subcategorySelectId);

    if (category) {
        const options = [];
        try {
            const response = await fetch(`/api/get_subcategory/?category=${category}`);
            const data = await response.json();

            // Enable the subcategory select and clear previous options
            tomSubCategory.enable();
            tomSubCategory.clear();
            tomSubCategory.clearOptions();

            // Add new options
            for (let subcat of data.subcategories) {
                options.push({
                    value: subcat[0],
                    text: subcat[1]
                });
            }

            // Add new options to TomSelect
            tomSubCategory.addOption(options);
            tomSubCategory.refreshItems();

        } catch (error) {
            console.log(error);
        }
    } else {
        // Clear and disable the subcategory select if no category is provided
        tomSubCategory.clear();
        tomSubCategory.clearOptions();
        tomSubCategory.disable();
    }
}
