# uncomment the CACHES section
startStr="#CACHES = {"
endStr="#}"
uncomment "/$startStr/,/$endStr/" "$CONFIG_FILE"

# use "redis" hostname for redis server
sed -i 's>redis://127.0.0.1>redis://redis>g' "$CONFIG_FILE"
