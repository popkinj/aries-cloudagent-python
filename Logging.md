# Logging docs

Acapy supports multiple configurations of logging.

## Log level

Acapy's logging is based on python's [logging lib](https://docs.python.org/3/howto/logging.html).
Log levels `DEBUG`, `INFO` and `WARNING` are available.
Other log levels fall back to `WARNING`.

## Command Line Arguments

* `--log-level` - The log level to log on std out.
* `--log-file` - Path to a file to log to.
* `--log-config` - Specifies a custom logging configuration file


Example:

```sh
./bin/aca-py start --log-level debug --log-file acapy.log --log-config aries_cloudagent.config:default_per_tenant_logging_config.ini

./bin/aca-py start --log-level debug --log-file acapy.log --log-config ./aries_cloudagent/config/default_per_tenant_logging_config.yml
```

## Environment Variables

The log level can be configured using the environment variable `ACAPY_LOG_LEVEL`.
The log file can be set by `ACAPY_LOG_FILE`.
The log config can be set by `ACAPY_LOG_CONFIG`.

Example:

```sh
ACAPY_LOG_LEVEL=info ACAPY_LOG_FILE=./acapy.log ACAPY_LOG_CONFIG=./acapy_log.ini ./bin/aca-py start
```

## Acapy Config File

Following parameters can be used in a configuration file like [this](demo/demo-args.yaml).

```yaml
log-level: WARNING
debug-connections: false
debug-presentations: false
```

Warning: debug-connections and debug-presentations must not be used in a production environment as they log also credential claims values.
Both parameters are independent of the log level, which means:
Also if log-level is set to WARNING, connections and presentations will be logged like in debug log level.

## Log config file

The path to config file is provided via `--log-config`.

Find an example in [default_logging_config.ini](aries_cloudagent/config/default_logging_config.ini).

You can find more detail description in the [logging documentation](https://docs.python.org/3/howto/logging.html#configuring-logging).

For per tenant logging, find an example in [default_per_tenant_logging_config.ini](aries_cloudagent/config/default_per_tenant_logging_config.ini), which sets up  `TimedRotatingFileMultiProcessHandler` and `StreamHandler` handlers. Custom `TimedRotatingFileMultiProcessHandler` handler supports the ability to cleanup logs by time and maintain backup logs and a custom JSON formatter for logs. The arguments for it such as `file name`, `when`, `interval` and `backupCount` can be passed as `args=('acapy.log', 'd', 7, 1,)` [also shown below]. Note: `backupCount` of 0 will mean all backup log files will be retained and not deleted at all. More details about these attributes can be found [here](https://docs.python.org/3/library/logging.handlers.html#timedrotatingfilehandler)

```
[loggers]
keys=root

[handlers]
keys=stream_handler, timed_file_handler

[formatters]
keys=formatter

[logger_root]
level=ERROR
handlers=stream_handler, timed_file_handler

[handler_stream_handler]
class=StreamHandler
level=DEBUG
formatter=formatter
args=(sys.stderr,)

[handler_timed_file_handler]
class=logging.handlers.TimedRotatingFileMultiProcessHandler
level=DEBUG
formatter=formatter
args=('acapy.log', 'd', 7, 1,)

[formatter_formatter]
format=%(asctime)s %(wallet_id)s %(levelname)s %(pathname)s:%(lineno)d %(message)s
```

For `DictConfig` [`dict` logging config file], find an example in [default_per_tenant_logging_config.yml](aries_cloudagent/config/default_per_tenant_logging_config.yml) with same attributes as `default_per_tenant_logging_config.ini` file.

```
version: 1
formatters:
  default:
    format: '%(asctime)s %(wallet_id)s %(levelname)s %(pathname)s:%(lineno)d %(message)s'
handlers:
  console:
    class: logging.StreamHandler
    level: DEBUG
    formatter: default
    stream: ext://sys.stderr
  rotating_file:
    class: logging.handlers.TimedRotatingFileMultiProcessHandler
    level: DEBUG
    filename: 'acapy.log'
    when: 'd'
    interval: 7
    backupCount: 1
    formatter: default
root:
  level: INFO
  handlers:
    - console
    - rotating_file
```
