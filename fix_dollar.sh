#!/bin/bash
# Futtatás: bash fix_dollar.sh
# A projekt gyökérkönyvtárából

find app/templates -name "*.html" | while read file; do
    # $0.00 -> 0 Ft
    sed -i 's/\${{ "%.2f"|format(\([^)]*\)) }}/{{ "%.0f"|format(\1) }} Ft/g' "$file"
    # $0 -> 0 Ft (egyszerű változók)
    sed -i 's/\${{ \([^}]*\) }}$/{{ \1 }} Ft/g' "$file"
    # Revenue ($) -> Bevétel (Ft)
    sed -i "s/Revenue (\\\$)/Bevétel (Ft)/g" "$file"
    # '\$' + v -> v + ' Ft'
    sed -i "s/'\\\$' + v/v + ' Ft'/g" "$file"
    echo "Fixed: $file"
done
echo "Kész!"
