# Built-in Dependencies
import subprocess
import platform
import logging
import socket
import os

# Third-Party Dependencies
import psutil


def _parse_positive_int(value: str | int | None, default: int = 1) -> int:
    """Convert lscpu field values; '-' / empty / non-numeric fall back to default."""
    if value is None:
        return default
    if isinstance(value, int):
        return value
    text = str(value).strip()
    if not text or text == "-":
        return default
    try:
        return int(text)
    except ValueError:
        return default


def _format_cpu_speed() -> str:
    """Return CPU max frequency, or 'unknown' when cpufreq is unavailable."""
    cpu_freq = psutil.cpu_freq()
    if cpu_freq is None or cpu_freq.max is None:
        return "unknown"
    return f"{cpu_freq.max:.2f} MHz"


def log_system_info(logger: logging.Logger) -> None:
    # Obtain username and machine IP
    user_name = os.getenv("USER") or os.getenv("LOGNAME") or os.getenv("USERNAME")
    ip_address = socket.gethostbyname(socket.gethostname())

    try:
        # Run 'lscpu' command to get detailed CPU information on Linux
        cpu_info_process = subprocess.run(["lscpu"], capture_output=True, text=True)
        cpu_info_output = cpu_info_process.stdout

        # Extract relevant CPU information
        relevant_info = [
            "Architecture",
            "CPU op-mode(s)",
            "Model name",
            "CPU family",
            "Model",
            "Thread(s) per core",
            "Core(s) per socket",
            "Socket(s)",
            "Virtualization",
        ]

        relevant_cpu_info = {
            info.strip(): line.split(":", 1)[1].strip()
            for line in cpu_info_output.splitlines()
            if (info := line.split(":", 1)[0].strip()) in relevant_info
        }

        # Log with detailed information, including relevant CPU details
        logger.info(
            f"API started on machine: system={platform.system()}, user={user_name}, IP={ip_address}, "
            f"RAM_available={psutil.virtual_memory().available / (1024**3):.2f} GB, "
            f"machine_model_name='{relevant_cpu_info.get('Model name', '')}', "
            f"threads_per_core={_parse_positive_int(relevant_cpu_info.get('Thread(s) per core'))}, "
            f"cores_per_socket={_parse_positive_int(relevant_cpu_info.get('Core(s) per socket'))}, "
            f"sockets={_parse_positive_int(relevant_cpu_info.get('Socket(s)'))}, "
            f"virtualization='{relevant_cpu_info.get('Virtualization', '')}', "
            f"CPU_cores={psutil.cpu_count(logical=False)}, CPU_speed={_format_cpu_speed()}"
        )
    except FileNotFoundError:
        # Use platform.processor() on Windows if 'lscpu' is not available
        cpu_info_output = (
            f"Model name: {platform.processor()}, "
            f"Physical cores: {psutil.cpu_count(logical=False)}, "
            f"Total cores: {psutil.cpu_count(logical=True)}"
        )
        logger.info(
            f"API started on machine: system={platform.system()}, user={user_name}, IP={ip_address}, "
            f"RAM_available={psutil.virtual_memory().available / (1024**3):.2f} GB, "
            f"{cpu_info_output}, "
            f"CPU_cores={psutil.cpu_count(logical=False)}, CPU_speed={_format_cpu_speed()}"
        )
    except Exception as e:
        # Log an error if there's an issue retrieving CPU information
        logger.error(f"Error getting CPU information: {e}")
