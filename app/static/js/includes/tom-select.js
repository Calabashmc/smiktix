export function tommifyField(fieldToSet, maxitems, customRender = null, extraOptions = {}) {
    maxitems = maxitems || 10;

    const tommifiedField = new TomSelect(fieldToSet, {
        placeholder: 'Select...',
        maxItems: maxitems,
        maxOptions: null,
        closeAfterSelect: true,
        valueField: 'value',
        labelField: 'text',
        searchField: 'text',
        hideSelected: true,
        create: false,
        selectOnTab: true,
        allowEmptyOption: false,
        render: customRender || {},
        ...extraOptions // overrides default settings so I can make hideSelected false for avatar selection
    });

    return tommifiedField;
}

// Map of TomSelect instances
export const tomSelectInstances = new Map();

export async function initaliseTomSelectFields() {
    const customSelectFields = document.querySelectorAll('.custom-select, .custom-multi-select');

    for (const field of customSelectFields) {
        let parameter = field.classList.contains('custom-select') ? 1 : 10;

        // Special case for avatar field to add icons and scroll current selection into view
        if (field.id === 'avatar') {
            const avatarInstance = tommifyField(field, parameter, null, {
                hideSelected: false  // 👈 This allows re-selection and visibility
            });

            avatarInstance.settings.render = {
                // option is how the option is displayed - so have larger image
                option: function (data, escape) {
                    return `<div class="option">
                      <img src="${escape(data.value)}" alt="${escape(data.text)}"
                           style="width:50px; height:50px; vertical-align:middle; margin-right:10px;">
                      ${escape(data.text)}
                    </div>`;
                },
                // item is the selection so image can be smaller as it is shown in the image next to the select.
                item: function (data, escape) {
                    return `<div class="item">
                      <img src="${escape(data.value)}" alt="${escape(data.text)}"
                           style="width:20px; height:20px; vertical-align:middle; margin-right:5px;">
                      ${escape(data.text)}
                    </div>`;
                }
            };

            avatarInstance.setupTemplates();

            avatarInstance.on('dropdown_open', function () {
                const selectedOption = this.getValue();
                const optionEl = this.dropdown_content.querySelector(
                    `[data-value="${CSS.escape(selectedOption)}"]`
                );

                if (optionEl) {
                    optionEl.scrollIntoView({block: 'nearest'});
                }
            });


            // ✅ Only re-render if a value is set (avoid null remove error)
            const currentValue = avatarInstance.getValue();
            if (currentValue) {
                avatarInstance.setValue(null, true); // Clear safely
                avatarInstance.setValue(currentValue, true); // Re-set to trigger rendering
            }

            tomSelectInstances.set(field.id, avatarInstance);
            continue;
        }

        // Default init
        const instance = tommifyField(field, parameter);
        tomSelectInstances.set(field.id, instance);
    }
}

