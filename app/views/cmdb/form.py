import os
from flask import current_app, url_for
from sqlalchemy import select

from app.common.forms import UserDetailsMixin, BaseMixin
from wtforms import (
    BooleanField,
    DateField,
    FloatField,
    IntegerField,
    SelectMultipleField,
    SelectField,
    StringField,
    TextAreaField
)
from wtforms.validators import Optional, InputRequired, DataRequired, Length
from ...model import db
from ...model.lookup_tables import (
    DeliveryMethodLookup,
    Importance,
    PlatformLookup,
    SupportTypeLookup,
    VendorLookup, ChangeFreezeReasonLookup, HostingLookup
)
from ...model.lookup_tables import ModelLookup
from ...model.model_category import Category
from ...model.model_cmdb import CmdbHardware, OperatingSystem, CmdbSoftware
from ...model.model_user import Team, User
from ...model.relationship_tables import category_model


class CmdbForm(UserDetailsMixin, BaseMixin):
    def __init__(self, *args, **kwargs):
        super(CmdbForm, self).__init__(*args, **kwargs)

        def select_icon():
            icons_folder = 'vis-network'
            # Get the path to the static folder using Flask's app context
            static_folder = current_app.static_folder
            icons_folder_path = os.path.join(static_folder, 'images', icons_folder)

            icon_files = os.listdir(icons_folder_path)
            # Construct URLs for each image file
            image_urls = [url_for('static', filename=f'images/{icons_folder}/{file}') for file in icon_files]

            # Create tuples with (full URL, filename) for choices
            choices = [(url, os.path.basename(url)) for url in image_urls]
            # Sort choices alphabetically by the filename
            choices.sort(key=lambda x: x[1])
            return choices

        self.category_id.choices = [("", "")] + [
            (el.id, el.name)
            for el in db.session.execute(
                select(Category)
                .join(category_model)  # Join the association table
                .join(ModelLookup)  # Join the ModelLookup table
                .where(ModelLookup.name == "Cmdb")  # Filter for the desired name
            ).scalars().all()
        ]

        self.change_freeze_reason.choices = [("", "")] + [
            (el.id, el.reason) for el in
            db.session.execute(
                select(ChangeFreezeReasonLookup)
                .order_by(ChangeFreezeReasonLookup.reason.asc())
            ).scalars().all()
        ]

        self.delivery_method.choices = [("", "")] + [
            (el.id, el.delivery_method) for el in
            db.session.execute(
                select(DeliveryMethodLookup)
                .order_by(DeliveryMethodLookup.delivery_method.asc())
            ).scalars().all()
        ]

        self.icons.choices = [("", "")] + select_icon()

        self.importance_id.choices = [("", "")] + [
            (el.id, el.importance) for el in
            db.session.execute(
                select(Importance)
                .order_by(Importance.id.asc())
            ).scalars().all()
        ]

        self.owner_id.choices = [("", "")] + [
            (el.id, el.full_name)
            for el in
            db.session.execute(
                select(User)
                .where(User.active == True)
                .order_by(User.username.asc())
            ).scalars().all()
        ]

        self.operating_system_id.choices = [("", "")] + [
            (el.id, el.os + " " + el.flavour if el.flavour else el.os)
            for el in db.session.execute(
                select(OperatingSystem)
                .order_by(OperatingSystem.os.asc())
            ).scalars().all()
        ]

        self.support_team_id.choices = [("", "")] + [
            (el.id, el.name) for el in
            db.session.execute(
                select(Team)
                .order_by(Team.name.asc())
            ).scalars().all()
        ]

        self.support_type.choices = [("", "")] + [
            (el.id, el.support_type) for el in db.session.execute(
                select(SupportTypeLookup)
                .order_by(SupportTypeLookup.support_type.asc())
            ).scalars().all()
        ]

        self.vendor_sales_id.choices = [("", "")] + [
            (el.id, el.vendor) for el in db.session.execute(
                select(VendorLookup)
                .order_by(VendorLookup.vendor.asc())
            ).scalars().all()
        ]

        self.vendor_support_id.choices = self.vendor_sales_id.choices

    brand = StringField(
        id="brand",
        label="Brand",
        render_kw={"class": "dirty"}
    )

    category_id = SelectField(
        label="Category",
        id="category-id",
        choices=[],
        validators=[InputRequired()],
        render_kw={"class": "custom-select dirty"}
    )

    change_freeze_start_date = DateField(
        id="change-freeze-start-date",
        label="Change Freeze Start Date",
        validators=[Optional()],
        render_kw={"class": "dirty"}
    )

    change_freeze_end_date = DateField(
        id="change-freeze-end-date",
        label="Change Freeze End Date",
        validators=[Optional()],
        render_kw={"class": "dirty"}
    )

    change_freeze_list = SelectMultipleField(
        id="change-freeze-list",
        label="Change Freeze List",
        choices=[],
        validators=[Optional()],
    )

    change_freeze_reason = SelectField(
        id="change-freeze-reason",
        label="Change Freeze Reason",
        choices=[],
        validate_choice=False,
    )

    change_freeze_title = StringField(
        id="change-freeze-title",
        label='Title (max 15 characters)',
        validators=[Optional(), Length(max=15, message="Title must be 15 characters or fewer.")]
    )

    icons = SelectField(
        id="ci-icons",
        choices=[],
        render_kw={"class": "dirty"}
    )

    # choices are populated in populate_relationship_select_choices() in ticket_utils.py to apply a filter
    # so exiting relationship is not listed
    compliance_select = SelectField(
        id="compliance-select",
        label="Compliance Standards",
        choices=[],
        validators=[Optional()],
        render_kw={"class": "custom-select", "style:": "font-family: monospace;"}
    )

    # choices are populated in the route for this one
    compliance_list = SelectMultipleField(
        id="compliance-list",
        label="Complies With",
        choices=[],
    )

    continuity_planning = BooleanField(
        id="continuity",
        label="Include in DR/Business Continuity Planning?",
        render_kw={"class": "dirty"}
    )

    cost_centre = StringField(
        id="cost-centre",
        label="Cost Centre",
        render_kw={"class": "dirty"}
    )

    delivery_method = SelectField(
        id="delivery-method",
        label="Delivery Method",
        choices=[],
        validate_choice=False,
        validators=[Optional()],
        render_kw={"class": "custom-select dirty"}
    )

    disposed_date = DateField(
        id="disposed-date",
        label="Disposed",
        validators=[Optional()],
        render_kw={"class": "dirty"}
    )

    end_life_date = DateField(
        id="end-life-date",
        label="End of Life",
        validators=[Optional()],
        render_kw={"class": "dirty"}
    )

    importance_id = SelectField(
        id="importance",
        label="Importance",
        validate_choice=False,
        choices=[],
        render_kw={"class": "custom-select dirty"}
    )

    install_date = DateField(
        id="install-date",
        label="Deployed",
        validators=[Optional()],
        render_kw={"class": "dirty"}
    )

    location = StringField(
        id="location",
        label="Location",
        render_kw={"class": "dirty"}
    )

    model = StringField(
        id="model",
        label="Model",
        render_kw={"class": "dirty"}
    )

    monitored_with = StringField(
        id="monitored-with",
        label="Monitored With",
        render_kw={"class": "dirty"}
    )

    name = StringField(
        id="name",
        label="Name",
        validators=[InputRequired()],
        render_kw={"class": "dirty"}
    )

    obtained_date = DateField(
        id="obtained-date",
        label="Built/Obtained",
        validators=[Optional()],
        render_kw={"class": "dirty"}
    )

    operating_system_id = SelectField(
        id="operating-system",
        label="Operating System",
        validators=[Optional()],
        render_kw={"class": "custom-select dirty"}
    )

    owner_id = SelectField(
        id="owner-id",
        label="Owner",
        validators=[DataRequired()],
        render_kw={"class": "custom-select owner dirty"}
    )

    purchase_price = StringField(
        id="purchase-price",
        label="Purchase Price",
        render_kw={"class": "dirty"}
    )

    purchase_order = StringField(
        id="purchase-order",
        label="Purchase Order",
        render_kw={"class": "dirty"},
    )

    replacement_date = DateField(
        id="replacement-date",
        label="Replaced",
        validators=[Optional()],
        render_kw={"class": "dirty"},
    )

    replaced_with_id = SelectField(
        id="replacement-node",
        label="Replaced With",
        choices=[],
        validators=[Optional()],
        render_kw={"class": "custom-select dirty"}
    )

    retirement_date = DateField(
        id="retirement-date",
        label="Retired",
        validators=[Optional()],
        render_kw={"class": "dirty"}
    )

    status = StringField(
        id="status",
        label="status",
        default="New",
        render_kw={"hidden": True, "class": "dirty", "form": "form"}
    )

    support_end_date = DateField(
        id="support-ends-date",
        label="Support Ends",
        validators=[Optional()],
        render_kw={"class": "dirty"}
    )

    support_team_id = SelectField(
        id="support-team",
        label="Support Team",
        validators=[InputRequired()],
        choices=[],
        render_kw={"class": "custom-select dirty", }
    )

    support_type = SelectField(
        id="support-type",
        label="Support Type",
        choices=[],
        validators=[Optional()],
        render_kw={"class": "custom-select dirty"}
    )

    twentyfour_operation = BooleanField(id="ci-operations-hours",
                                        label="24x7?",
                                        render_kw={"class": "dirty"},
                                        )

    upstream_node = SelectField(
        id="upstream-node",
        label="Select Upstream Device",
        choices=[],
        validate_choice=False,
        validators=[Optional()],
        render_kw={"class": "custom-select"}
    )

    upstream_list = SelectMultipleField(
        id="upstream-list",
        label="Upstream Node List",
        choices=[],
        validate_choice=False,
        validators=[Optional()],
    )

    vendor_sales_id = SelectField(
        id="vendor-sales-id",
        label="Vendor (Sales)",
        choices=[],
        validators=[Optional()],
        render_kw={"class": "custom-select dirty"}
    )

    vendor_sales_contact = StringField(
        id="vendor-sales-contact",
        label="Contact/Account Rep.",
        default="Contact unknown",
        render_kw={"readonly": True, "class": "no-border"},
    )

    vendor_sales_email = StringField(
        id="vendor-sales-email",
        label="Email",
        default="Email unknown",
        render_kw={"readonly": True, "class": "no-border"},
    )

    vendor_sales_phone = StringField(
        id="vendor-sales-phone",
        label="Phone",
        default="Phone unknown",
        render_kw={"readonly": True, "class": "no-border"},
    )

    vendor_support_id = SelectField(
        id="vendor-support-id",
        label="Vendor (Support)",
        choices=[],
        validators=[Optional()],
        render_kw={"class": "custom-select dirty"}
    )

    vendor_support_contact = StringField(
        id="vendor-support-contact",
        label="Contact/Account Rep.",
        default="Contact unknown",
        render_kw={"readonly": True, "class": "no-border"},
    )

    vendor_support_email = StringField(
        id="vendor-support-email",
        label="Email",
        default="Email unknown",
        render_kw={"readonly": True, "class": "no-border"},
    )

    vendor_support_phone = StringField(
        id="vendor-support-phone",
        label="Phone",
        default="Phone unknown",
        render_kw={"readonly": True, "class": "no-border"},
    )

    version = StringField(
        id="version",
        render_kw={"class": "dirty"}
    )


class CmdbHardwareForm(CmdbForm):
    def __init__(self, *args, **kwargs):
        super(CmdbHardwareForm, self).__init__(*args, **kwargs)

        self.replaced_with_id.choices = [("", "")] + [
            (el.id, f'{el.asset_tag} | {el.name}') for el in
            db.session.execute(
                select(CmdbHardware)
                .order_by(CmdbHardware.asset_tag.asc())
            ).scalars().all()
        ]

        self.vendor_warranty_id.choices = [("", "")] + [
            (el.id, el.vendor) for el in db.session.execute(
                select(VendorLookup)
                .order_by(VendorLookup.vendor.asc())
            ).scalars().all()
        ]

    asset_tag = StringField(
        id="asset-tag",
        label="Asset Tag",
        render_kw={"class": "dirty"}
    )

    capacity_cpu = StringField(
        label="CPU (GHz)",
        id="capacity-cpu",
        render_kw={"class": "dirty"}
    )

    capacity_memory = StringField(
        label="RAM (GB)",
        id="capacity-memory",
        render_kw={"class": "dirty"}
    )

    capacity_storage = StringField(
        label="Storage",
        id="capacity-storage"
    )

    capacity_throughput = StringField(
        label="Throughput (GB/s)",
        id="capacity-throughput",
        render_kw={"class": "dirty"}
    )

    downstream_node = SelectField(
        id="downstream-node",
        label="Select Downstream Node",
        choices=[],
        validate_choice=False,
        validators=[Optional()],
        render_kw={"class": "custom-select"}
    )

    downstream_list = SelectMultipleField(
        id="downstream-list",
        label="Downstream Node List",
        choices=[],
        validate_choice=False,
    )

    fixed_ip_address = StringField(
        label="Fixed IP Address",
        id="fixed-ip-address",
        render_kw={"class": "dirty"}
    )

    mac_address = StringField(
        label="MAC Address",
        id="mac-address",
        render_kw={"class": "dirty"}
    )

    operating_system = StringField(
        label="Operating System",
        id="operating-system",
        render_kw={"class": "dirty"}
    )

    purchase_date = DateField(
        label="Purchase Date",
        id="purchase-date",
        validators=[Optional()],
        render_kw={"class": "dirty"}
    )

    serial_number = StringField(
        label="Serial Number",
        id="serial-number",
        render_kw={"class": "dirty"}
    )

    ssid = StringField(
        label="SSID",
        id="ssid",
        render_kw={"class": "dirty"}
    )

    virtual_machine = BooleanField(
        id="virtual-machine",
        label="Virtual?",
        render_kw={"class": "dirty"}
    )

    warranty_expiration_date = DateField(
        id="warranty-expiration-date",
        label="Warranty Expires",
        validators=[Optional()],
        render_kw={"class": "dirty"}
    )

    vendor_warranty_id = SelectField(
        id="vendor-warranty-id",
        label="Warranty Provider",
        choices=[],
        validators=[Optional()],
        render_kw={"class": "custom-select dirty"}
    )

    vendor_warranty_contact = StringField(
        id="vendor-warranty-contact",
        label="Contact/Account Rep.",
        default="Contact unknown",
        render_kw={"readonly": True, "class": "no-border"},
    )

    vendor_warranty_email = StringField(
        id="vendor-warranty-email",
        label="Email",
        default="Email unknown",
        render_kw={"readonly": True, "class": "no-border"},
    )

    vendor_warranty_phone = StringField(
        id="vendor-warranty-phone",
        label="Phone",
        default="Phone unknown",
        render_kw={"readonly": True, "class": "no-border"},
    )

    wifi_password = StringField(
        id="wifi-password",
        label="WiFi Password",
        render_kw={"class": "dirty"}
    )


class CmdbSoftwareForm(CmdbForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.hosted.choices = [("", "")] + [
            (el.id, el.hosting)
            for el in db.session.execute(
                select(HostingLookup)
            ).scalars().all()
        ]

        self.supported_platforms.choices = [("", "")] + [
            (el.id, el.platform)
            for el in db.session.execute(
                select(PlatformLookup)
            ).scalars().all()
        ]

    hosted = SelectField(
        "Hosted",
        choices=[],
        validators=[Optional()],
        render_kw={"class": "dirty"}
    )

    host_name = StringField(
        label="Host Name",
        id="host-name",
        validators=[Optional()],
        render_kw={"class": "dirty"}
    )

    licence_cost = FloatField(
        label="Licence Cost",
        id="licence-cost",
        validators=[Optional()],
        render_kw={"class": "dirty"}
    )

    licence_count = IntegerField(
        id="licence-count",
        label="Licence Count",
        default=0,
        render_kw={"class": "dirty"}
    )

    licence_expiration_date = DateField(
        id="licence-expiration-date",
        label="Licence Expires",
        validators=[Optional()],
        render_kw={"class": "dirty"}
    )

    licence_key = StringField(
        label="Licence Key",
        id="licence-key",
        validators=[Optional()],
        render_kw={"class": "dirty"}
    )

    licence_type = StringField(
        label="Licence Type",
        id="licence-type",
        render_kw={"class": "dirty"}
    )

    maintenance_expires = DateField(
        label="Maintenance Expires",
        id="maintenance-expires",
        render_kw={"class": "dirty"}
    )

    supported_platforms = SelectField(
        label="Supported Platforms",
        id="supported-platforms",
        choices=[],
        validators=[Optional()],
        render_kw={"class": "custom-select dirty"}
    )


class CmdbNetworkDeviceForm(CmdbForm):
    ip_address = StringField(
        label="IP Address",
        id="ip-address",
        render_kw={"class": "dirty"}
    )

    mac_address = StringField(
        label="MAC Address",
        id="mac-address",
        render_kw={"class": "dirty"}
    )


class CmdbServiceForm(CmdbForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.downstream_node.choices = [("", "")] + [
            (el.id, f'{el.ticket_type} -> {el.ticket_number} | {el.name}') for el in
            db.session.execute(
                select(CmdbHardware)
                .order_by(CmdbHardware.name.asc())
            ).scalars()
        ] + [
            (el.id, f'{el.ticket_type} -> {el.ticket_number} | {el.name}') for el in
            db.session.execute(
                select(CmdbSoftware)
                .order_by(CmdbSoftware.name.asc())
            ).scalars()
        ]

    downstream_node = SelectField(
        id="downstream-node",
        label="Select Downstream Node",
        choices=[],
        validate_choice=False,
        validators=[Optional()],
        render_kw={"class": "custom-select"}
    )

    downstream_list = SelectMultipleField(
        id="downstream-list",
        label="Downstream Node List",
        choices=[],
        validate_choice=False,
    )

    provider = SelectField(
        label="Provider",
        id="provider",
        choices=[("Vendor", "Vendor"), ("Team", "Team")],  # todo make a lookup internal, SaaS, PaaS?
        validators=[Optional()],
        render_kw={"class": "custom-select dirty"}
    )

    business_criticality = SelectField(  # todo is this needed? Importance covers?
        "Business Criticality",
        choices=[("High", "High"), ("Medium", "Medium"), ("Low", "Low")],
        validators=[Optional()],
        render_kw={"class": "custom-select dirty"}
    )

    dependencies = TextAreaField("Dependencies", validators=[Optional()])

    interfaces = TextAreaField("Interfaces", validators=[Optional()])
    sla = StringField("Service Level Agreement")  # todo is this needed? Importance covers?
    start_date = DateField("Start Date", validators=[Optional()])

    end_date = DateField("End Date", validators=[Optional()])

    service_cost = FloatField("Service Cost", validators=[Optional()])
