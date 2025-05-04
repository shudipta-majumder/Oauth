class OpenApiTags:
    MENU_ROUTES = "menus"
    Authorization = "authorizations"
    Users = "user-management"
    Accounts = "accounts"
    DROPDOWN_REPO = "dropdown-repo"
    DROPDOWN_REPO_PMS = "pms-dropdown"
    DROPDOWN_REPO_PMS_BANK = "pms-bank-branch-dropdown"

    # Party
    PARTY = "party-routes"
    DEALINGS = "party-dealings-routes"
    ATTACHMENTS = "party-attachment-routes"
    EXTRA_ATTACHMENT = "extra-attachment-routes"
    CONTACTS = "party-contacts-routes"

    # Credit Limits
    PMS_CREDIT_LIMIT_APPLICATION = "credit-limit"
    PMS_CREDIT_LIMIT_DETAIL_APPLICATION = "credit-limit-detail"
    PMS_SHIP_LOCATION_APPLICATION = "ship-location"
    PMS_SECURITY_CHEQUE = "security-cheque"
    GUARANTOR = "guarantor-routes"

    EBS_ROUTES = "ebs-routes"

    #TMS
    TMS_SETUP = "tms-setup-routes"
    TMS_PRODUCT= "tms-product-routes"
    TMS_TENDER="tms-tender-routes"
    TMS_BG_EXTENDED_DATE = "tms-bg-extended-date-routes"
    PRE_TENDER_MEETING = "tms-pretender-meeting-routes"
    POST_NOA = "tms-post-noa-routes"
    CONTRACT_AGREEMENT = "tms-contract-agreement-routes"
    NOTIFICATION = "tms-notification-routes"
    VENDOR = "tms-vendor-routes"
    PAYMENT = "tms-payments-routes"
    TENDER_ANALYSIS ="tms-analysis-routes"
    PRODUCT_SPACIFICATION = "tms-product-spacification"


openapi_description = r"""
<img src="https://waltonbd.com/image/catalog/new_website/icon/logo/social_link_share_logo.jpg" width="200" height="100">

OSS provides a comprehensive suite of services tailored to streamline various aspects of organizational operations. From managing parties and guests to corporate price quotations, OSS offers efficient solutions to enhance productivity and effectiveness.

## 🟢 Party Management System (PMS)

The Party Management System (PMS) allows authorized users to access and manage party-related information within the system. It provides functionalities to create, update, delete, and retrieve details about parties. Users can easily handle party planning, scheduling, and tracking with this system.

## 🟡 Corporate Price Quotation (CPQ)

The Corporate Price Quotation (CPQ) service enables authorized users to retrieve corporate price quotations. It facilitates the generation of price estimates for corporate services and products offered by the organization. Users can generate accurate quotes tailored to specific corporate needs, ensuring transparency and efficiency in pricing.

## 🟡 Guest Management System (GMS)

The Guest Management System (GMS) empowers authorized users to manage guest-related information effectively. It provides functionalities to handle guest registrations, check-ins, and check-outs, ensuring seamless guest experiences. With GMS, users can maintain detailed guest records, streamline guest communication, and optimize guest satisfaction.

---
**Note:** This API is intended for authorized organizations and internal use only. Unauthorized access is strictly prohibited.
"""

SETTINGS_METADATA = {
    "OAS_VERSION": "3.1.0",
    "TITLE": r"One Stop Solution Service API",
    "DESCRIPTION": openapi_description,
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SCHEMA_PATH_PREFIX": r"/api/v[0-9]",
    "SWAGGER_UI_FAVICON_HREF": "https://waltondigitech.com/favicon/favicon-32x32.png",
    "SERVE_AUTHENTICATION": None,
    "SWAGGER_UI_SETTINGS": {
        "swagger": "2.0",
        "deepLinking": True,
        "filter": True,
        "persistAuthorization": True,
        "displayOperationId": True,
    },
    "POSTPROCESSING_HOOKS": [
        "drf_spectacular.contrib.djangorestframework_camel_case.camelize_serializer_fields",
        "drf_spectacular.hooks.postprocess_schema_enums",
    ],
    "SERVERS": [
        {"url": "http://127.0.0.1:8000", "description": "LOCAL DEV"},
        {"url": "http://192.168.16.81:8000", "description": "LOCAL TEST"},
        {"url": "http://192.168.117.201:8001", "description": "STAGING TEST"},
        {"url": "http://192.168.16.20:8000", "description": "SOURAV"},
        {"url": "https://ossapi.waltonbd.com:8008", "description": "PRODUCTION"}
    ],
    "COMPONENT_SPLIT_REQUEST": True,
}
