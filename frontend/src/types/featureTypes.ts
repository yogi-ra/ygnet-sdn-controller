export enum ViewFeatureType {
    DISPLAY_TABLE = "display_table",
    DISPLAY_TEXT = "display_text",
}

export enum ActionFeatureType {
    TOGGLE = "toggle",
    INPUT_TEXT = "input_text",
    SELECT_OPTION = "select_option",
    BUTTON = "button",
    TEXT_AREA = "text_area",
}

export type FeatureType = ViewFeatureType | ActionFeatureType;

export enum HeaderFieldType {
    TEXT = "text",
    STATISTIC = "statistic",
    STATUS = "status",
}

export interface FeatureOption {
    label: string;
    value: string;
}

export interface FeatureDependency {
    feature_name: string;
    operator: "equals" | "not_equals";
    value: string | boolean | number;
}

export interface TableAction {
    feature_name: string;
    backend_method: string;
}

export interface ViewFeatureSchema {
    name: string;
    label: string;
    description?: string;
    type: ViewFeatureType;
    backend_method: string;
    group?: string;
    order?: number;
    actions?: TableAction[];
    row_identifier?: string;
}

export interface ActionFeatureSchema {
    name: string;
    label: string;
    description?: string;
    type: ActionFeatureType;
    backend_method: string;
    default_value?: any;
    options?: FeatureOption[];
    placeholder?: string;
    dependencies?: FeatureDependency[];
    validationRules?: {
        pattern?: string;
        minLength?: number;
        maxLength?: number;
        errorMessage?: string;
    };
    group?: string;
    order?: number;
}

export type FeatureSchema = ViewFeatureSchema | ActionFeatureSchema;

export interface HeaderFieldSchema {
    name: string;
    label: string;
    type: HeaderFieldType;
    value?: any;
    unit?: string;
    format?: string;
    order?: number;
}

export interface FeatureActionRequest {
    feature_name: string;
    value?: any;
}

export interface DeviceFeaturesResponse {
    view_features: ViewFeatureSchema[];
    action_features: ActionFeatureSchema[];
    header_fields: HeaderFieldSchema[];
    groups: string[];
}
