export enum FeatureType {
    TOGGLE = "toggle",
    INPUT_TEXT = "input_text",
    DISPLAY_TABLE = "display_table",
    DISPLAY_TEXT = "display_text",
    SELECT_OPTION = "select_option",
    BUTTON = "button",
}

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

export interface FeatureSchema {
    name: string;
    label: string;
    description?: string;
    type: FeatureType;
    read_only: boolean;
    default_value?: any;
    options?: FeatureOption[];
    placeholder?: string;
    dependencies?: FeatureDependency[];
    backend_method?: string;
    backend_command?: string;
    group?: string;
    order?: number;
    display_location?: "header";
}

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
    features: FeatureSchema[];
    header_fields: HeaderFieldSchema[];
}
// This is a no-op change to trigger a rebuild.