function enrich_log_record(tag, timestamp, record)
    -- Rename log to log_message if present
    if record["log"] then
        record["log_message"] = record["log"]
        record["log"] = nil
    end

    -- List of known container names
    local known_names = {
        "api-gateway",
        "frontend",
        "influxdb",
        "grafana",
        "qdrant",
        "redis",
        "influx-client",
        "rag-chatbot",
        "nginx",
        "forecasting",
        "fluent-bit"
    }

    -- Search for a known name in the log message
    if record["log_message"] then
        for _, name in ipairs(known_names) do
            if string.find(record["log_message"], name) then
                record["container_name"] = name
                break
            end
        end
    end

    -- Fallback from the tag
    if not record["container_name"] and tag then
        local container_name = string.match(tag, "docker%.([^.]+)")
        if container_name then
            record["container_name"] = container_name
        end
    end

    -- Extract image name if present
    if not record["image_name"] and record["log_message"] then
        local image = string.match(record["log_message"], 'image=([%w%p]+)')
        if image then
            record["image_name"] = image
        end
    end

    -- Extract log level
    if record["log_message"] then
        local lvl = string.match(record["log_message"], "(%u+):")
        if lvl and (#lvl <= 7) then
            record["log_level"] = lvl
        end
    end

    -- Clean up fields
    if record["stream"] then
        record["status"] = record["stream"]
        record["stream"] = nil
    end
    -- Optionally extract exit_code if present
    if record["log_message"] then
        local exit_code = string.match(record["log_message"], "exit code[:= ](%d+)")
        if exit_code then
            record["exit_code"] = tonumber(exit_code)
        end
    end
    return 1, timestamp, record
end
