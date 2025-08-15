#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

LOG_PID=""

usage() {
	cat <<'USAGE'
Usage: scripts/dev_run.sh <command> [--with-logs]

Commands:
  up               Build and start containers (api, worker, db, redis)
  logs             Follow api and worker logs
  submit-example   Submit examples/basic.qasm3 and poll until completion
  async-test       Run tests/test_async_multi_submit.py inside the api container
  e2e-test         Run tests/test_api_end_to_end.py inside the api container
  all-tests        Run the whole /app/tests suite inside the api container

Flags:
  --with-logs      Stream logs concurrently while running submit-example or tests

Examples:
  scripts/dev_run.sh logs
  scripts/dev_run.sh submit-example --with-logs
  scripts/dev_run.sh async-test --with-logs
  scripts/dev_run.sh e2e-test --with-logs
  scripts/dev_run.sh all-tests
USAGE
}

up() {
	echo "[dev] building images..."
	docker compose build api worker >/dev/null
	echo "[dev] starting services..."
	docker compose up -d
}

stream_logs() {
	docker compose logs -f api worker
}

submit_example() {
	if [[ ! -f examples/basic.qasm3 ]]; then
		echo "examples/basic.qasm3 not found" >&2
		return 1
	fi
	local qasm
	qasm=$(tr -d '\n' < examples/basic.qasm3 | sed 's/"/\\"/g')
	echo "[dev] submitting example..."
	local resp
	resp=$(curl -s -X POST http://localhost:8000/tasks -H 'content-type: application/json' --data-binary "{\"qc\": \"$qasm\"}")
	echo "[dev] submit response: $resp"
	local id
	id=$(sed -n 's/.*"task_id":"\([^"]*\)".*/\1/p' <<<"$resp")
	if [[ -z "$id" ]]; then
		echo "[dev] could not parse task_id from response" >&2
		return 1
	fi
	echo "[dev] polling task $id ..."
	for _ in $(seq 1 60); do
		local body status
		body=$(curl -s http://localhost:8000/tasks/$id)
		echo "[dev] poll: $body"
		status=$(sed -n 's/.*"status":"\([^"]*\)".*/\1/p' <<<"$body")
		[[ "$status" == "completed" ]] && return 0
		sleep 1
	done
	echo "[dev] timeout waiting for completion" >&2
	return 1
}

copy_tests_into_api() {
	echo "[dev] copying tests into api container..."
	local cid
	cid=$(docker compose ps -q api)
	docker cp tests "$cid":/app/ >/dev/null
}

async_test() {
	copy_tests_into_api
	echo "[dev] running async multi-submit test..."
	docker compose exec -T api python -m pytest -q /app/tests/test_async_multi_submit.py
}

e2e_test() {
	copy_tests_into_api
	echo "[dev] running end-to-end API test..."
	docker compose exec -T api python -m pytest -q /app/tests/test_api_end_to_end.py
}

all_tests() {
	copy_tests_into_api
	echo "[dev] running full test suite..."
	docker compose exec -T api python -m pytest -q /app/tests
}

start_logs_bg() {
	stream_logs &
	LOG_PID=$!
}

stop_logs_bg() {
	if [[ -n "${LOG_PID}" ]]; then
		kill "${LOG_PID}" >/dev/null 2>&1 || true
		LOG_PID=""
	fi
}

main() {
	local cmd="${1:-}"
	local with_logs="false"
	shift || true
	if [[ "${1:-}" == "--with-logs" ]]; then
		with_logs="true"
		shift || true
	fi

	case "$cmd" in
		u|up)
			up
			;;
		l|logs)
			up
			stream_logs
			;;
		submit-example)
			up
			if [[ "$with_logs" == "true" ]]; then
				start_logs_bg
				submit_example
				stop_logs_bg
			else
				submit_example
			fi
			;;
		async-test)
			up
			if [[ "$with_logs" == "true" ]]; then
				start_logs_bg
				async_test
				stop_logs_bg
			else
				async_test
			fi
			;;
		e2e-test)
			up
			if [[ "$with_logs" == "true" ]]; then
				start_logs_bg
				e2e_test
				stop_logs_bg
			else
				e2e_test
			fi
			;;
		all-tests)
			up
			if [[ "$with_logs" == "true" ]]; then
				start_logs_bg
				all_tests
				stop_logs_bg
			else
				all_tests
			fi
			;;
		*)
			usage
			return 1
			;;
	 esac
}

main "$@"
