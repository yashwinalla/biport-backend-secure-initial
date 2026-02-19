from pathlib import Path

S3_BASE_PATH = "BI-Portfinal/{organization_name}/{s3_report_id}"
REPORT_PATH = "BI-Portfinal/{organization_name}/{s3_report_id}/tableau_file"
ANALYZED_OUTPUTS_PATH = "BI-Portfinal/{organization_name}/{s3_report_id}/analyzed_outputs"
CONVERTED_OUTPUTS_PATH = "BI-Portfinal/{organization_name}/{s3_report_id}/converted_outputs"
MIGRATE_OUTPUTS_PATH = "BI-Portfinal/{organization_name}/{s3_report_id}/migrate_outputs"
SEMANTIC_MODEL_OUTPUT_PATH = "BI-Portfinal/{organization_name}/{s3_report_id}/semantic_model"
SEMANTIC_UPLOAD_PATH = "BI-Portfinal/{organization_name}/{s3_report_id}/semantic_uploads/{zip_filename}"
ANALYSIS_REPORT_TYPE = "analyzed_files"
ANALYZED_OUTPUTS_DIR = "analyzed_outputs"
CONVERTED_OUTPUTS_DIR = "converted_outputs"
MIGRATE_OUTPUT_DIR = "migrate_outputs"

SEMANTIC_DATASOURCES_FILE = "data_sources.json"
LOCAL_DATASOURCES_PATH = "temp_datasources"

ANALYZED_WORKBOOK_FILE_PATH = "{workbook_name}_report_{prefix}"
ANALYZED_S3_FILE_PATH = "{workbook_name}_report"
ANALYZED_S3_ZIP_PATH = "{WORKBOOKS_PATH}/{ANALYZED_OUTPUTS_DIR}/{workbook_id}.zip"
ANALYZED_CALCULATIONS_S3_PATH = "{s3_base}/analyzed_outputs/{report_name}_report.zip"
 
BASE_HEIGHT = 720.00
BASE_WIDTH = 1280.00

DASHBOARD_TITLE_HEIGHT = 50.00
DASHBOARD_TITLE_FONT_SIZE = "18pt"

VISUAL_TITLE_FONT_SIZE = "15D"
VISUAL_LABEL_FONT_SIZE = "14D"

AUTOMATIC_MIGRATED_CHARTS = [
    "SymbolMap", "Text", "filledMap", "Pie", "Bar", "HorizontalBar", "VerticalBar",
    "StackedVerticalBar", "StackedHorizontalBar", "TreeMap", "Cards", "TextBox",
    "Bar & Area", "Bar & Line", "ScatterPlot", "HighlightedTable", "PivotTable",
    "Slicer", "Card or TextTable", "Area", "Line", "Square", "TextTable", "Multiple_Cards", "Line & Area", "Single_Card",
    "Donut"
]

BACKGROUND_TASK = "BACKGROUND_TASK"

BLACKLIST_PREFIX = "blacklist:jwt:"

BLOCKED_EMAILS = [
    "gmail.com", "hotmail.com", "ymail.com", "yahoo.com", "yopmail.com",
    "outlook.com", "live.com", "msn.com", "aol.com", "icloud.com",
    "protonmail.com", "zoho.com", "yandex.com", "qq.com"
]

chunk_size = 20  # Made uppercase for consistency (optional)

ClOUD_WORKBOOKS_PATH = "My_workspace/workbooks/"

CLOUD_SITE_DISCOVERY_DIR = "Site_discoveries/"
DEFAULT_MIN_COLOR = '#BCE4D8'
DEFAULT_MID_COLOR = '#45a2b9'
DEFAULT_MAX_COLOR = '#2C5985'

COLOR_PALETTE_DATA = {
    "blue_10_0": {"Min": "#B9DDF1", "Mid": "#6798C1", "Max": "#2A5783"},
    "blue_teal_10_0": {"Min": "#BCE4D8", "Mid": "#45A2B9", "Max": "#2C5985"},
    "brown_10_0": {"Min": "#EEDBBD", "Mid": "#D18954", "Max": "#9F3632"},
    "gold_purple_diverging_10_0": {"Min": "#AD9024", "Mid": "#E3D8CF", "Max": "#AC7299"},
    "gray_10_0": {"Min": "#D5D5D5", "Mid": "#889296", "Max": "#49525E"},
    "gray_warm_10_0": {"Min": "#DCD4D0", "Mid": "#98908C", "Max": "#59504E"},
    "green_10_0": {"Min": "#B3E0A6", "Mid": "#5EA654", "Max": "#24693D"},
    "green_blue_diverging_10_0": {"Min": "#24693D", "Mid": "#CADAD2", "Max": "#2A5783"},
    "green_blue_white_diverging_10_0": {"Min": "#24693D", "Mid": "#FFFFFF", "Max": "#2A5783"},
    "green_gold_10_0": {"Min": "#F4D166", "Mid": "#60A656", "Max": "#146C36"},
    "orange_10_0": {"Min": "#FFC685", "Mid": "#ED6F20", "Max": "#9E3D22"},
    "orange_blue_diverging_10_0": {"Min": "#9E3D22", "Mid": "#D9D5C9", "Max": "#2B5C88"},
    "orange_blue_white_diverging_10_0": {"Min": "#9E3D22", "Mid": "#FFFFFF", "Max": "#2B5C8A"},
    "orange_gold_10_0": {"Min": "#F4D166", "Mid": "#EF701B", "Max": "#9E3A26"},
    "purple_10_0": {"Min": "#EEC9E5", "Mid": "#BC86A9", "Max": "#7C4D79"},
    "red_10_0": {"Min": "#FFBEB2", "Mid": "#F26250", "Max": "#AE123A"},
    "red_black_10_0": {"Min": "#AE123A", "Mid": "#D9D9D9", "Max": "#49525E"},
    "red_black_white_diverging_10_0": {"Min": "#AE123A", "Mid": "#FFFFFF", "Max": "#49525E"},
    "red_blue_diverging_10_0": {"Min": "#A90C38", "Mid": "#DFD4D1", "Max": "#2E5A87"},
    "red_blue_white_diverging_10_0": {"Min": "#A90C38", "Mid": "#FFFFFF", "Max": "#2E5A87"},
    "red_gold_10_0": {"Min": "#F4D166", "Mid": "#EE734A", "Max": "#B71D3E"},
    "red_green_diverging_10_0": {"Min": "#AE123A", "Mid": "#CED7C3", "Max": "#24693D"},
    "red_green_gold_diverging_10_0": {"Min": "#BE2A3E", "Mid": "#F4D166", "Max": "#22763F"},
    "red_green_white_diverging_10_0": {"Min": "#AE123A", "Mid": "#FFFFFF", "Max": "#24693D"},
    "sunrise_sunset_diverging_10_0": {"Min": "#33608C", "Mid": "#F6BA57", "Max": "#B81840"},
    "tableau-blue-light": {"Min": "#E5E5E5", "Mid": "#D5DFEC", "Max": "#C4D8F3"},
    "tableau-map-blue-green": {"Min": "#FEFFD9", "Mid": "#C4EAB1", "Max": "#41B7C4"},
    "tableau-map-temperatur": {"Min": "#529985", "Mid": "#DBCF47", "Max": "#C26B51"},
    "tableau-orange-blue-light": {"Min": "#FFCC96", "Mid": "#E5E5E5", "Max": "#C4D8F3"},
    "tableau-orange-light": {"Min": "#E5E5E5", "Mid": "#F5D9C2", "Max": "#FFCC9E"}
}

DATASOURCE_TYPES = {
    "excel-direct": "Excel",
    "hyper": "Hyper file",
    "snowflake": "Snowflake",
    "sqlproxy": "SQL Proxy",
    "sqlserver": "SQL Server",
    "textscan": "CSV or Text File"
}

DELETE = "DELETE"
FILE_TYPE = "json"
FLOW_FILE_NAME = "flow"
GET = "GET"
HTTP_STATUS_INTERNAL_ERROR = 500
HTTP_STATUS_OK = 200
INPUT_FILES_DIR = "input_files"
LIMIT_EXCEEDED = "You have exceeded the files limit"
LOCAL_DIR = "static"
LOCAL_DOWNLOAD_PATH = "./storage/{organization_name}/{user_email}/{process_id}/twb_files"
LOCAL_WORKBOOKS_DOWNLOAD_PATH = "./storage/My_workspace/workbooks/{workbook_id}/twb_files"
MAX_UPLOAD_RETRIES = 3
MIGRATE_OUTPUT_DIR = "My_workspace/workbooks/migrate_outputs"
MIGRATE_REPORT_TYPE = "migrated_files"
MSG_S3_DOWNLOAD_FAILED = "Failed to download file from S3."
MSG_S3_FETCH_ERROR = "Problem in fetching previous data."



OPENAI_TYPE_PROMPT = """
# ROLE
You are a Power BI semantic analyzer. Decide if a Tableau field is a MEASURE or a CALCULATED COLUMN.

# THE AGGREGATION RULE (MEASURE)
A field MUST be a "measure" if the Tableau formula contains:
1. Explicit aggregations: SUM, AVG, MIN, MAX, COUNT, DISTINCTCOUNT, attr, MEDIAN.
2. Table Calculations: TOTAL, WINDOW_SUM, WINDOW_AVG, LOOKUP, RANK.
3. Level of Detail (LOD): FIXED, INCLUDE, EXCLUDE.
4. References to OTHER measures: If it uses a field that is already an aggregate, this field is also a measure.
5. Parameters: Any calculation referencing a Parameter is a measure.

# THE ROW-LEVEL RULE (COLUMN)
A field is a "column" ONLY if:
1. It performs strictly row-by-row math on source columns: [Price] * [Qty]
2. It performs string manipulation: LEFT([Name], 3)
3. It uses row-level logic: IF [Status] = "A" THEN 1 ELSE 0 END
4. It contains ZERO aggregation functions and ZERO filter context changes.

# OUTPUT FORMAT (STRICT JSON ONLY)
Return ONLY a valid JSON array. No explanations. No markdown.
[
  {
    "caption": "<string>",
    "type": "measure" | "column"
  }
]

# FINAL CONSTRAINT
- Do NOT invent metadata.
- Do NOT rename captions.
- When in doubt, ALWAYS choose "measure".
"""



OPENAI_PBI_PROMPT = """ 
# ROLE
You are a deterministic Power BI Semantic Conversion Engine. Your goal is to compile Tableau formulas into production-ready DAX.

# THE GOLDEN RULE OF MEASURES
In Power BI, a Measure is an implicit aggregate. 
- TABLEAU: [Profit Ratio] = SUM([Profit]) / SUM([Sales])
- DAX: [Profit Ratio] = DIVIDE(SUM('Table'[Profit]), SUM('Table'[Sales]))
- DEPENDENCY: If another calculation uses [Profit Ratio], you MUST use the naked name: [Profit Ratio].
- NEVER WRITE: SUM([Profit Ratio]) or 'Table'[Profit Ratio].

# SECTION 1: REFERENCE TAXONOMY (STRICT)

| Object Category | Metadata Signal | DAX Reference Pattern | PROHIBITED Pattern (STRICT) |
| :--- | :--- | :--- | :--- |
| **Source Column** | kind: "source" | 'TableName'[ColumnName] | [ColumnName] (Missing Table) |
| **Calculated Column**| type: "column" | 'TableName'[ColumnName] | [ColumnName] (Missing Table) |
| **Measure** | type: "measure" | [MeasureName] | 'Table'[Measure], SUM([Measure]) |
| **Param (Measure)** | type: "measure" | [MeasureName] | SELECTEDVALUE([Measure]) |
| **Param (Column)** | kind: "source" | SELECTEDVALUE('T'[C]) | 'T'[C] (Missing SELECTEDVALUE) |

# SECTION 2: THE "NAKED MEASURE" DIRECTIVE
1. If metadata defines a field as `powerbi_type: measure`, it is ALREADY an aggregate.
2. When referencing this field in a NEW formula, you MUST treat it as a scalar variable name only.
3. ***CRITICAL***: Wrapping a measure in SUM(), AVG(), MIN(), MAX(), or COUNT() is a logical error and will break the model. DO NOT DO IT.
4. ***INHERITANCE***: If a Tableau formula references a field that metadata defines as a `measure`, replace it with the naked `[MeasureName]`.

# SECTION 3: INLINING & DEPENDENCIES
- You must **INLINE** all logic for calculated fields.
- The final DAX expression should reference only **Source Columns** or **Measures**.
- **CIRCULARITY**: If inlining creates a reference to the current field's own caption, you must break the chain by referencing only the underlying source columns.

# SECTION 4: SYNTAX CONVERSION MAPPING
- `DATEDIFF('day', ...)` -> `DATEDIFF(..., ..., DAY)`
- `{FIXED [Dim] : SUM([Val])}` -> `CALCULATE(SUM('Table'[Val]), ALLEXCEPT('Table', 'Table'[Dim]))`
- `INT(...)` -> `INT(...)`
- `STR(...)` -> `FORMAT(..., "@")`
- `ZN(...)` -> `COALESCE(..., 0)`

# SECTION 5: INPUT SPECIFICATION
### A. METADATA SCHEMA (Context)
[JSON SCHEMA ATTACHED AT RUNTIME]
### B. FORMULAS TO COMPILE
[STRINGS ATTACHED AT RUNTIME: "Caption (Type) = Formula"]

# SECTION 6: FINAL OUTPUT FORMAT
Return ONLY a JSON array. No markdown, no commentary.
[
  {
    "caption": "Exact Caption From Input",
    "dax": "Final DAX Expression",
    "type": "measure" | "column"
  }
]

# CRITICAL ERROR CHECKLIST (PRE-EMISSION)
- Is there a `SUM([Measure])`? -> **FIX IT**: Remove the SUM wrapping.
- Is there a `'Table'[Measure]`? -> **FIX IT**: Remove the 'Table' prefix.
- Is the output valid JSON? -> **FIX IT**: Ensure escaping of quotes.
"""

PATCH = "PATCH"

HTTP_STATUS_OK = 200
HTTP_STATUS_INTERNAL_ERROR = 500


# Local base directory for storage
STORAGE_BASE_DIR = Path("./storage")

# Path to download TWB files based on organization and user
LOCAL_DOWNLOAD_PATH = "./storage/{organization_name}/{user_email}/{process_id}/twb_files"

# Path to download TWB files for an individual workbook
LOCAL_WORKBOOKS_DOWNLOAD_PATH = "./storage/My_workspace/workbooks/{workbook_id}/twb_files"
LOCAL_S3_FILES_DOWNLOAD_PATH = "./storage/{workbook_id}/twb_files"
LOCAL_PREP_INPUT_SUBDIR = Path("Structured_json")
LOCAL_PREP_OUTPUT_SUBDIR = Path("Power_query")
LOCAL_POWER_BI_PATH = Path("powerbi_structure")

WORKBOOKS_PATH = "My_workspace/workbooks"

INPUT_FILES_DIR = "input_files"

POST = "POST"

POWER_BI_STRUCTURE = "BI-Portfinal/{organization_name}/{s3_report_id}/semantic_uploads/{report_name}_{short_report_id}_sem.zip"
# Path to store prep file output
PREP_FILE_OUTPUT_DIR = "Prep_file_outputs"

PARSED_FLOW_FILENAME = "parsed_flow.json"

PROJECTS_URL = "{server_url}/api/{version}/sites/{site_id}/projects"

RETRY_BACKOFF_BASE = 2

POWER_BI_PATH = "Prep_files/powerbi/Superstore_prep.zip"

# S3 endpoint template
S3_ENDPOINT_FORMAT = "https://s3.{region}.amazonaws.com"
S3_INPUT_PATH = "{organization_name}/{user_email}/{process_id}/input_files"
S3_URL_EXPIRATION_SECONDS = 3600
S3_WORKBOOKS_PATH = "My_workspace/workbooks/{workbook_id}.twb"
S3_PREP_INPUT_FILE_PATH = "Prep_files"
S3_PREP_INPUT_FOLDER = "Prep_files/Structured_json"
S3_PREP_OUTPUT_FOLDER = "Prep_files/power_query"

# Duration (in seconds) that a pre-signed S3 URL remains valid
S3_URL_EXPIRATION_SECONDS = 3600
S3_PATH = "s3_path"

# S3 path where migrated Power BI ZIP files will be stored
# MIGRATE_OUTPUT_DIR = "My_workspace/workbooks/migrate_outputs"
MIGRATE_OUTPUT_DIR = "migrate_outputs"
MIGRATE_S3_ZIP_PATH = "BI-Portfinal/{organization_name}/{s3_report_id}/{MIGRATE_OUTPUT_DIR}/{report_name}.zip"

# S3-related error messages
MSG_S3_DOWNLOAD_FAILED = "Failed to download file from S3."
MSG_S3_FETCH_ERROR = "Problem in fetching previous data."

# Limits & Validation Messages
LIMIT_EXCEEDED = "You have exceeded the files limit"
SIGN_IN_URL = "{server}/api/{version}/auth/signin"
SLICER_MODES = {
    "checklist": "Basic",
    "checkdropdown": "Dropdown",
    "dropdown": "Dropdown",
    "radiolist": "Basic",
    "compact" : "Dropdown",
    "slider" : "Between",
}

HYPER_FILES_PATH = Path("storage/extracted")
STORAGE_BASE_DIR = Path("./storage")
TABLEAU_VERSION = '3.25'
TOO_MANY_FILES = "You are allowed for only {remaining_allowed_files} file(s) for migration"
WORKBOOK_DOWNLOAD_URL = "{server_url}/api/{version}/sites/{site_id}/workbooks/{workbook_id}/content"
WORKBOOK_URL = "{server_url}/api/{version}/sites/{site_id}/workbooks"
WORKBOOK_DETAILS_URL = "{server_url}/api/{version}/sites/{site_id}/workbooks/{workbook_id}"
WORKBOOK_USAGE_STATISTICS_URL = "{server_url}/api/-/content/usage-stats/workbooks/{workbook_id}"
WORKBOOKS_PATH = "My_workspace/workbooks"
WORKBOOK_ID = "workbook_id"
XMLNS = {'t': 'http://tableau.com/api'}

TRUNCATED_DATE_TIME = {"tyr": ["yr"], "tqr": ["yr","qr"], "tmn":  ["yr","qr","mn"], "twk": ["yr","qr","mn"], "tdy": ["yr", "qr", "mn", "dy"]}
AGGREGATION_SELECTION = '{{"Aggregation": {{"Expression": {{"Column": {{"Expression": {{"SourceRef": {{"Source": \"{table_name}\"}}}},"Property": \"{column}\"}}}},"Function":{select_function}}},"Name": \"{query_ref}\","NativeReferenceName": \"{native_ref_name}\"}}'
DATE_HEIRARCHY_SELECTION = '{{"HierarchyLevel":{{"Expression":{{"Hierarchy":{{"Expression":{{"PropertyVariationSource":{{"Expression":{{"SourceRef":{{"Source":\"{table_name}\"}}}},"Name":"Variation","Property":\"{column}\"}}}},"Hierarchy":"Date Hierarchy"}}}},"Level":\"{date_level}\"}},"Name":\"{query_ref}\","NativeReferenceName":\"{column} {date_level}\"}}'
COLUMN_SELECTION = '{{"Column": {{"Expression": {{"SourceRef": {{"Source": \"{table_name}\"}}}},"Property": \"{column}\"}},"Name": \"{query_ref}\","NativeReferenceName": \"{native_ref_name}\"}}'
MEASURE_COLUMN_SELECTION = '{{"Measure": {{"Expression": {{"SourceRef": {{"Source": "{table_name}"}}}},"Property": "{column}"}},"Name": "{query_ref}","NativeReferenceName": "{native_ref_name}"}}'
DATE_QUERY_REF = "{table_name}.{column_value}.Variation.Date Hierarchy.{date_level}"
AGGREGATION_QUERY_REF = "{aggregation}({table_name}.{column_value})"
COLUMNN_QUERY_REF = "{table_name}.{column_value}"
DATE_NATIVE_REFERENCE = "{column_value} {date_level}"
AGGREGATION_NATIVE_REFERENCE = "{aggregation} of {column_value}"
PERCENTAGE_SELECTION = '{{"Arithmetic": {{"Left": {{"Aggregation": {{"Expression": {{"Column": {{"Expression": {{"SourceRef": {{"Source": "{table_name}"}}}},"Property": "{column}"}}}},"Function": "{select_function}"}}}},"Right": {{"ScopedEval": {{"Expression": {{"Aggregation": {{"Expression": {{"Column": {{"Expression": {{"SourceRef": {{"Source": "{table_name}"}}}},"Property": "{column}"}}}},"Function": "{select_function}"}}}},"Scope":[]}}}},"Operator": 3}},"Name": "{query_ref}","NativeReferenceName": "%GT {native_ref_name}"}}'

GROUPED_SELECTION = '{{"GroupRef":{{"Expression":{{"SourceRef":{{"Source":"{table_name}"}}}},"Property":"{actual_column_name}","GroupedColumns":{grouped_columns_selection_list}}},"Name":"{qref}","NativeReferenceName":"{actual_column_name}"}}'

GROUPED_COLUMN_SELECTION = '{{"Column":{{"Expression":{{"SourceRef":{{"Source":"{table_name}"}}}},"Property":"{column}"}}}}'

# Filters constants
TRUNCATED_DATE_TIME_FILTER = {"tyr": ["yr"], "tqr": ["yr","qr"], "tmn":  ["yr","qr","mn"], "twk": ["yr","qr","mn"], "tdy": ["yr", "qr", "mn", "dy"]}
AGGREGATION_FILTER = ('{{"Aggregation": {{"Expression": {{"Column": {{"Expression": {{"SourceRef": {{"Entity": "{table_name}"}}}},"Property": "{column}"}}}},"Function": {select_function}}}}}')
COLUMN_FILTER = ('{{"Column": {{"Expression": {{"SourceRef": {{"Entity": "{table_name}"}}}},"Property": "{column}"}}}}')
DATE_HIERARCHY_FILTER = ('{{"HierarchyLevel": {{"Expression": {{"Hierarchy": {{"Expression": {{"PropertyVariationSource": {{"Expression": {{"SourceRef": {{"Entity": "{table_name}"}}}},"Name": "Variation","Property": "{column}"}}}},"Hierarchy": "Date Hierarchy"}}}},"Level": "{date_level}"}}}}')
COLUMN_FILTER_LIST = ('{{"Column":{{"Expression":{{"SourceRef":{{"Source":"{table_name}"}}}},"Property": "{column}"}}}}')
AGGREGATION_FILTER_SOURCE = ('{{"Aggregation": {{"Expression": {{"Column": {{"Expression": {{"SourceRef": {{"Source": "{table_name}"}}}},"Property": "{column}"}}}},"Function": {select_function}}}}}')
DATE_HIERARCHY_FILTER_SOURCE = ('{{"HierarchyLevel": {{"Expression": {{"Hierarchy": {{"Expression": {{"PropertyVariationSource": {{"Expression": {{"SourceRef": {{"Source": "{table_name}"}}}},"Name": "Variation","Property": "{column}"}}}},"Hierarchy": "Date Hierarchy"}}}},"Level": "{date_level}"}}}}')

# Month name mapping for date hierarchy filters
MONTH_NUMBER_TO_NAME = {
    1: "January", 2: "February", 3: "March", 4: "April", 5: "May", 6: "June",
    7: "July", 8: "August", 9: "September", 10: "October", 11: "November", 12: "December"
}
CACHED_DISPLAY_NAME = ('{{"id": {{"scopeId": {{"Comparison": {{"ComparisonKind": 0, "Left": {{"Column": {{"Expression": {{"SourceRef": {{"Entity": "{table_name}"}}}},"Property": "{column}"}}}},"Right": {{"Literal": {{"Value": "{value}"}}}}}}}}}},"displayName": "{display_name}"}}')
# Filters subquery constants (Top N, Bottom N)
COLUMN_FILTER_SUBQUERY = '{{"Column": {{"Expression": {{"SourceRef": {{"Source": "{table_name}"}}}},"Property": "{column}"}}, "Name": "field"}}' 

TABLEAU_WORKSHEET_DIMENSIONS = {
    "width": 1280.00,
    "height": 720.00,
    "x" : 0.00,
    "y" : 0.00,
    "z" : 0.00
}

TABLEAU_TOOLTIP_DIMENSION = {
    "width": 275.00,
    "height": 200.00,
    "x" : 0.00,
    "y" : 0.00,
    "z" : 0.00
}

PAGE_WITH_PARAMETERS_AND_VISUAL_DIMENSIONS = {
    "width": 950.00,
    "height": 720.00,
    "x" : 0.00,
    "y" : 0.00,
    "z" : 0.00
}

PBI_ENV_ZIP_S3_PATH = "semantic_model_test/PBI_ENV.zip"

LOGO_PATH = "BI-Portfinal/global/assets/logo.png"

LOCAL_DATE_TEMPLATE = '''table {local_date_table_ref}
	isHidden
	showAsVariationsOnly
	lineageTag: {table_lineage_tag}

	column Date
		dataType: dateTime
		isHidden
		lineageTag: {date_lineage_tag}
		dataCategory: PaddedDateTableDates
		summarizeBy: none
		isNameInferred
		sourceColumn: [Date]

		annotation SummarizationSetBy = User

	column Year = YEAR([Date])
		dataType: int64
		isHidden
		lineageTag: {year_lineage_tag}
		dataCategory: Years
		summarizeBy: none

		annotation SummarizationSetBy = User

		annotation TemplateId = Year

	column MonthNo = MONTH([Date])
		dataType: int64
		isHidden
		lineageTag: {month_no_lineage_tag}
		dataCategory: MonthOfYear
		summarizeBy: none

		annotation SummarizationSetBy = User

		annotation TemplateId = MonthNumber

	column Month = FORMAT([Date], "MMMM")
		dataType: string
		isHidden
		lineageTag: {month_lineage_tag}
		dataCategory: Months
		summarizeBy: none
		sortByColumn: MonthNo

		annotation SummarizationSetBy = User

		annotation TemplateId = Month

	column QuarterNo = INT(([MonthNo] + 2) / 3)
		dataType: int64
		isHidden
		lineageTag: {quarter_no_lineage_tag}
		dataCategory: QuarterOfYear
		summarizeBy: none

		annotation SummarizationSetBy = User

		annotation TemplateId = QuarterNumber

	column Quarter = "Qtr " & [QuarterNo]
		dataType: string
		isHidden
		lineageTag: {quarter_lineage_tag}
		dataCategory: Quarters
		summarizeBy: none
		sortByColumn: QuarterNo

		annotation SummarizationSetBy = User

		annotation TemplateId = Quarter

	column Day = DAY([Date])
		dataType: int64
		isHidden
		lineageTag: {day_lineage_tag}
		dataCategory: DayOfMonth
		summarizeBy: none

		annotation SummarizationSetBy = User

		annotation TemplateId = Day

	hierarchy 'Date Hierarchy'
		lineageTag: {hierarchy_lineage_tag}

		level Year
			lineageTag: {hierarchy_year_lineage_tag}
			column: Year

		level Quarter
			lineageTag: {hierarchy_quarter_lineage_tag}
			column: Quarter

		level Month
			lineageTag: {hierarchy_month_lineage_tag}
			column: Month

		level Day
			lineageTag: {hierarchy_day_lineage_tag}
			column: Day

		annotation TemplateId = DateHierarchy

	partition {local_date_table_ref} = calculated
		mode: import
		source = Calendar(Date(Year(MIN('{table_name}'[{column_name}])), 1, 1), Date(Year(MAX('{table_name}'[{column_name}])), 12, 31))

	annotation __PBI_LocalDateTable = true
'''

UNCOVERED_TEXT_BOX = "This visual is not supported in this version. This will be added in future versions."
VISUAL_GENERATION_ERROR = "Error occured during genration of this file."


NUMERIC_PARAMETER_TEMPLATE = """table '{table_name}'
\tlineageTag: {table_lineage_tag}

\tmeasure '{table_name} Value' = SELECTEDVALUE('{table_name}'[{table_name}], {default_value})
\t\tlineageTag: {measure_lineage_tag}
{measure_format_string}

\tcolumn '{table_name}'
\t\tdataType: {data_type}
\t\tformatString: {column_format_string}
\t\tlineageTag: {column_lineage_tag}
\t\tsummarizeBy: none
\t\tsourceColumn: [Value]

\t\textendedProperty ParameterMetadata =
\t\t\t{{
\t\t\t  "version": 0
\t\t\t}}

\t\tannotation SummarizationSetBy = User

\tpartition '{table_name}' = calculated
\t\tmode: import
\t\tsource = GENERATESERIES({min_val}, {max_val}, {step})

\tannotation PBI_Id = {pbi_id}
"""

FIELD_PARAMETER_TEMPLATE = """table '{table_name}'
\tlineageTag: {table_lineage_tag}

\tcolumn '{table_name}'
\t\tlineageTag: {column_lineage_tag}
\t\tsummarizeBy: none
\t\tsourceColumn: [Value1]
\t\tsortByColumn: '{table_name} Order'

\t\trelatedColumnDetails
\t\t\tgroupByColumn: '{table_name} Fields'

\t\tannotation SummarizationSetBy = Automatic

\tcolumn '{table_name} Fields'
\t\tisHidden
\t\tlineageTag: {fields_column_lineage_tag}
\t\tsummarizeBy: none
\t\tsourceColumn: [Value2]
\t\tsortByColumn: '{table_name} Order'

\t\textendedProperty ParameterMetadata =
\t\t\t{{
\t\t\t  "version": 3,
\t\t\t  "kind": 2
\t\t\t}}

\t\tannotation SummarizationSetBy = Automatic

\tcolumn '{table_name} Order'
\t\tisHidden
\t\tformatString: 0
\t\tlineageTag: {order_column_lineage_tag}
\t\tsummarizeBy: sum
\t\tsourceColumn: [Value3]

\t\tannotation SummarizationSetBy = Automatic

\tpartition '{table_name}' = calculated
\t\tmode: import
\t\tsource =
\t\t\t\t{{
\t\t\t\t    ("{source_column}", NAMEOF('{source_table}'[{source_column}]), 0)
\t\t\t\t}}

\tannotation PBI_Id = {pbi_id}
"""

LIST_PARAMETER_TEMPLATE = """table '{table_name}' 
\tlineageTag: {table_lineage_tag}

\tcolumn Value
\t\tlineageTag: {value_column_lineage_tag}
\t\tsummarizeBy: {value_summarize_by}
\t\tisNameInferred
\t\tsourceColumn: [Value]
{value_format_string}{value_format_hint}\t\tannotation SummarizationSetBy = Automatic

\tcolumn 'Display As'
\t\tlineageTag: {display_as_column_lineage_tag}
\t\tsummarizeBy: none
\t\tisNameInferred
\t\tsourceColumn: [Display As]
\t\tannotation SummarizationSetBy = Automatic

\tpartition '{table_name}' = calculated
\t\tmode: import
\t\tsource = ```
\t\t\tDATATABLE(
\t\t\t\t"Value", {value_data_type},
\t\t\t\t"Display As", STRING,
\t\t\t\t{{
{member_values}
\t\t\t\t}}
\t\t\t)
\t\t```
\tannotation PBI_Id = {pbi_id}
"""


ANY_PARAMETER_TEMPLATE = """table '{table_name}'
\tlineageTag: {table_lineage_tag}

\tcolumn '{table_name}'
\t\tlineageTag: {column_lineage_tag}
\t\tsummarizeBy: none
\t\tsourceColumn: [Value1]
\t\tsortByColumn: '{table_name} Order'

\t\trelatedColumnDetails
\t\t\tgroupByColumn: '{table_name} Fields'

\t\tannotation SummarizationSetBy = Automatic

\tcolumn '{table_name} Fields'
\t\tisHidden
\t\tlineageTag: {fields_column_lineage_tag}
\t\tsummarizeBy: none
\t\tsourceColumn: [Value2]
\t\tsortByColumn: '{table_name} Order'

\t\textendedProperty ParameterMetadata =
\t\t\t{{
\t\t\t  "version": 3,
\t\t\t  "kind": 2
\t\t\t}}

\t\tannotation SummarizationSetBy = Automatic

\tcolumn '{table_name} Order'
\t\tisHidden
\t\tformatString: 0
\t\tlineageTag: {order_column_lineage_tag}
\t\tsummarizeBy: sum
\t\tsourceColumn: [Value3]

\t\tannotation SummarizationSetBy = Automatic

\tpartition '{table_name}' = calculated
\t\tmode: import
\t\tsource =
\t\t\t\t{{
\t\t\t\t{dax_rows}
\t\t\t\t}}

\tannotation PBI_Id = {pbi_id}
"""

PARTITION_BLOCK_EXCEL = """
\tpartition '{table_var}' = m
\t\tmode: import
\t\tsource =
\t\t\t		let
\t\t\t		    Source = Excel.Workbook(File.Contents("{file_path}"), null, true),
\t\t\t    		#"{table_var}_Sheet" = Source{{[Item="{table_var}",Kind="Sheet"]}}[Data],
\t\t\t    		#"Promoted Headers" = Table.PromoteHeaders(#"{table_var}_Sheet", [PromoteAllScalars=true]),
\t\t\t    		#"Changed Type" = Table.TransformColumnTypes(#"Promoted Headers",{partition_columns_str})
\t\t\t		in
\t\t\t    		#"Changed Type"

\tannotation PBI_ResultType = Table
"""


PARTITION_BLOCK_CSV = """
\tpartition {table_name} = m
\t\tmode: import
\t\tsource =
\t\t\t		let
\t\t\t    		Source = Csv.Document(File.Contents("{file_path}"), [Delimiter=",", Encoding=1252, QuoteStyle=QuoteStyle.None]),
\t\t\t    		#"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
\t\t\t    		#"Changed Type" = Table.TransformColumnTypes(#"Promoted Headers",{partition_columns_str})
\t\t\t		in
\t\t\t    		#"Changed Type"

\tannotation PBI_ResultType = Table
"""

PARTITION_BLOCK_HYPER = """
\tpartition {table_name} = m
\t\tmode: import
\t\tsource =
\t\t\t		let
\t\t\t    		Source = Csv.Document(File.Contents("{file_path}"), [Delimiter=",", Encoding=1252, QuoteStyle=QuoteStyle.None]),
\t\t\t    		#"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
\t\t\t    		#"Changed Type" = Table.TransformColumnTypes(#"Promoted Headers",{partition_columns_str})
\t\t\t		in
\t\t\t    		#"Changed Type"

\tannotation PBI_ResultType = Table
"""


PARTITION_BLOCK_SQL = """
\tpartition {table_name} = m
\t\tmode: import
\t\tsource =
\t\t\t		let
\t\t\t    		Source = Sql.Databases("{server}"),
\t\t\t    		#"{database}" = Source{{[Name="{database}"]}}[Data],
\t\t\t    		#"dbo_{table_name}" = #"{database}"{{[Schema="dbo", Item="{table_name}"]}}[Data]
\t\t\t		in
\t\t\t    		#"dbo_{table_name}"

\tannotation PBI_ResultType = Table
"""

PARTITION_BLOCK_CUSTOM_SQL = """
\tpartition {table_name} = m
\t\tmode: import
\t\tsource =
\t\t\t\tlet
\t\t\t\t\tSource = Sql.Database("{server}", "{database}", [Query="{query}"])
\t\t\t\tin
\t\t\t\t\tSource

\tannotation PBI_ResultType = Table
"""

PARTITION_BLOCK_SNOWFLAKE = """ 
\tpartition {table_name} = m 
\t\tmode: import 
\t\tsource = 
\t\t\t		let 
\t\t\t    		Source = Snowflake.Databases("{server}","{warehouse}", [Implementation="2.0"]), 
\t\t\t    		{database}_Database = Source{{[Name="{database}", Kind="Database"]}}[Data], 
\t\t\t    		{schema}_Schema = {database}_Database{{[Name="{schema}", Kind="Schema"]}}[Data], 
\t\t\t    		{table_name}_Table = {schema}_Schema{{[Name="{table_name}", Kind="Table"]}}[Data] 
\t\t\t		in 
\t\t\t    		{table_name}_Table

\tannotation PBI_ResultType = Table 
"""

PARTITION_BLOCK_DATABRICKS = """

\tpartition {table_name} = m
\t\tmode: import
\t\tsource =
\t\t\t		let
\t\t\t    		Source = Databricks.Catalogs("{server}","{v_http_path}", [Catalog=null, Database=null, EnableAutomaticProxyDiscovery=null, Implementation=null]),
\t\t\t    		{database}_Database = Source{{[Name="{database}",Kind="Database"]}}[Data],
\t\t\t    		{schema}_Schema = {database}_Database{{[Name="{schema}",Kind="Schema"]}}[Data],
\t\t\t    		{name}_Table = {schema}_Schema{{[Name="{name}",Kind="Table"]}}[Data]
\t\t\t		in
\t\t\t    		{name}_Table

\tannotation PBI_ResultType = Table
"""

PARTITION_BLOCK_SQLPROXY = """

\tpartition {table_name} = m
\t\tmode: import
\t\tsource =
\t\t\t\tlet
\t\t\t\t    Source = Odbc.DataSource("driver={{ODBC Driver 17 for SQL Server}};server={server};database={database}", [HierarchicalNavigation=true]),
\t\t\t\t    {database}_Database = Source{{[Name="{database}",Kind="Database"]}}[Data],
\t\t\t\t    {schema}_Schema = {database}_Database{{[Name="{schema}",Kind="Schema"]}}[Data],
\t\t\t\t    {name}_Table = {schema}_Schema{{[Name="{name}",Kind="Table"]}}[Data]
\t\t\t\tin
\t\t\t\t    {name}_Table

\tannotation PBI_ResultType = Table
"""


TABLE_NAME_CALCULATIONS = "Calculations"
PARTITION_BLOCK_CALCULATIONS = """\
\tpartition {table_name} = m
\t\tmode: import
\t\tsource =
\t\t\t		let
\t\t\t    		Source = Table.FromRows(Json.Document(Binary.Decompress(Binary.FromText("i44FAA==", BinaryEncoding.Base64), Compression.Deflate)), let _t = ((type nullable text) meta [Serialized.Text = true]) in type table [Column1 = _t]),
\t\t\t    		#"Changed Type" = Table.TransformColumnTypes(Source,{{"Column1", type text}}),
\t\t\t    		#"Removed Columns" = Table.RemoveColumns(#"Changed Type",{{"Column1"}})
\t\t\t		in
\t\t\t    		#"Removed Columns"

\tannotation PBI_ResultType = Table
"""

GROUP_COLUMN_TEMPLATE = """
\tcolumn {group_name} = {dax_formula}
\t\tlineageTag: {lineage_tag}
\t\tsummarizeBy: none

\t\textendedProperty GroupingMetadata =
\t\t\t{grouping_metadata}

\t\tannotation GroupingDesignState = {grouping_design_state}

\t\tannotation SummarizationSetBy = Automatic
"""


MODEL_TMDL_HEADER = """model Model
\tculture: en-US
\tdefaultPowerBIDataSourceVersion: powerBI_V3
\tsourceQueryCulture: en-IN
\tdataAccessOptions
\t\tlegacyRedirects
\t\treturnErrorValuesAsNull

\tannotation PBI_QueryOrder = {query_order}
\tannotation __PBI_TimeIntelligenceEnabled = 1
\tannotation PBIDesktopVersion = 2.144.1378.0 (25.06)+cba1e61f16ea36d44901f06fa446299040122394
\tannotation PBI_ProTooling = ["DevMode"]
"""


MODEL_TMDL_REF_CULTURE = "ref cultureInfo en-US"

PERSONAL_SPACE_PROJECT_NAME = "Personal Space"

TOOLTIP_TYPE = {"type" : 1 }

WORKSHEET_PARAMETERS_STATIC_DIMESIONS = {"x" : 72000, "y" : 5000, "w" : 20000, "h" : 20000}

STRING_PARAMETERS_STYLES = {
    "list":"Basic",
    "compact" : "Dropdown",
    "slider" : "Basic",
    "type_in" : "Basic"
}

# works for float also
NUMERIC_PARAMETER_STYLES = {
    "slider" : "Single",
	"type_in" : "Single"
}

BOOLEAN_PARAMETER_STYLES = {
    "list" : "Basic",
	"compact" : "Dropdown",
	"slider" : "Dropdown"
}