# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, 'thue_gtgt_app')

# Test GCS parser
from parsers.gcs_parser import parse_gcs
result = parse_gcs('GCS.pdf')
print('=== GCS Parser ===')
print(f'Detail rows: {len(result["detail"])}')
print('Summary:')
print(result['summary'].to_string())
print(f'Totals: {result["totals"]}')
print()

# Test GL parser
from parsers.gl_parser import parse_gl_tk511
result2 = parse_gl_tk511('GL_0903_TK511.pdf')
print('=== GL TK511 Parser ===')
print(f'Data rows: {len(result2["data"])}')
print('By product:')
print(result2['by_product'].to_string())
print(f'Totals: {result2["totals"]}')
print()

# Test TA030 TK3331
from parsers.ta030_parser import parse_ta030
result3 = parse_ta030('TA_030_TK3331.pdf', account_type='output')
print('=== TA030 TK3331 Parser ===')
print(f'Data rows: {len(result3["data"])}')
print(f'Opening balance: {result3["opening_balance"]:,.0f}')
print(f'Totals: {result3["totals"]}')
if not result3["data"].empty:
    print('Status counts:')
    print(result3["data"]["trang_thai"].value_counts().to_string())
print()

# Test TA035
from parsers.ta035_parser import parse_ta035
result4 = parse_ta035('TA_035_TK33311.pdf')
print('=== TA035 Parser ===')
print(f'Data rows: {len(result4["data"])}')
print('By product:')
print(result4['by_product'].to_string())
print(f'Totals: {result4["totals"]}')
print()

# Test TA036
from parsers.ta036_parser import parse_ta036
result5 = parse_ta036('TA_036_TK13311.pdf')
print('=== TA036 Parser ===')
print(f'Data rows: {len(result5["data"])}')
print('By category:')
print(result5['by_category'].to_string())
print(f'Totals: {result5["totals"]}')
