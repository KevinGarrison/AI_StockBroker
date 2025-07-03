-- Author: Ilef Kalboussi --

function extract_container_name(tag, timestamp, record)
    local log_file = record["log"]
    local container_id = record["container_id"]
    if not container_id and record["filename"] then
        container_id = string.match(record["filename"], "/var/lib/docker/containers/([a-f0-9]+)/")
    end
    if container_id then
        record["container_id"] = container_id
    end
    return 1, timestamp, record
end
