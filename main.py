from LogicWeave import LogicWeave, BankVoltage, GPIOMode
import time

def bypass_error_and_log(uart, log_file_path, msg):
    """
    Reads from UART, logging all data to a file until a newline sequence is found.
    This function avoids screen updates and focuses purely on data logging.

    Args:
        uart: The UART object from LogicWeave.
        log_file_path: The path to the file to write the log data.
        msg: The initial message to write to the UART.
    """
    print("Starting bypass error and logging to file...")
    
    # Write the initial message to the UART
    uart.write(msg.encode())
    
    # Open the file in append mode.
    with open(log_file_path, 'a') as f:
        # Loop to read until we find a full "\r\n" sequence.
        # This uses a simple sliding window of the last two bytes.
        last_two_bytes = b''
        while True:
            one_byte = uart.read(1)
            if not one_byte:
                continue # Skip empty reads

            # Write the received byte to the file
            f.write(one_byte.decode(errors='ignore'))
            
            # Update the sliding window
            last_two_bytes += one_byte
            if len(last_two_bytes) > 2:
                last_two_bytes = last_two_bytes[-2:]

            if last_two_bytes == b'\r\n':
                print("Newline sequence found. Bypassing startup error completed.")
                return

def read_until_end_and_log(uart, log_file_path, msg, name):
    """
    Reads from UART and logs all data to a file until an [END] token is found.
    This function handles token checking for [START], [RESULT], and [END].
    It will retry on 'Unexpected response' errors while preserving the buffer.

    Args:
        uart: The UART object from LogicWeave.
        log_file_path: The path to the file to write the log data.
        msg: The initial message to write to the UART.
        name: A name for the test (e.g., "BIT", "ATP").
    """
    print(f"Starting read until end and logging to file for {name} test...")
    
    # Write the initial message to the UART
    uart.write(msg.encode())

    # Open the file in append mode.
    with open(log_file_path, 'a') as f:
        full_buffer = ""
        while True:
            try:
                # Read a small chunk of data from the UART
                chunk = uart.read(32, 1)
                
                # If a read is successful, continue processing.
                if not chunk:
                    continue
                
                # Decode the chunk and print to console for real-time viewing
                decoded_chunk = chunk.decode(errors='ignore')
                print(decoded_chunk, end='')
                
                # Write the chunk to the file and flush to ensure it's written immediately
                f.write(decoded_chunk)
                f.flush()
                
                full_buffer += decoded_chunk
                
                # Check for tokens in the accumulated buffer
                if "[END]" in full_buffer:
                    print(f"\n[END] token found. {name} test completed and logged.")
                    return
                
                if "[RESULT]" in full_buffer:
                    result_start = full_buffer.find("[RESULT]") + len("[RESULT]")
                    if len(full_buffer) >= result_start + 4:
                        result_payload = full_buffer[result_start:result_start+4]
                        print(f"\nResult found: {result_payload}")
                        return
                        
            except Exception as e:
                if "Unexpected response" in str(e):
                    print(f"\nCaught expected error: {e}. Retrying read for {name} test...")
                    continue  # Loop back to retry the uart.read()
                else:
                    print(f"\nAn unexpected error occurred during {name} test: {e}")
                    raise # Re-raise other exceptions

# --- Main Script ---

if __name__ == '__main__':
    # File paths for logging
    bit_log_file = "bit.txt"
    atp_log_file = "atp.txt"
    
    # Clearing the files from previous runs for a fresh start.
    open(bit_log_file, 'w').close()
    open(atp_log_file, 'w').close()

    try:
        with LogicWeave() as lw:
            ch1 = lw.pd_channel(1)
            ch2 = lw.pd_channel(2)
            
            ch1.request_power(voltage_mv=15000, current_limit_ma=2500)
            ch2.request_power(voltage_mv=5000, current_limit_ma=2000)
            
            lw.write_bank_voltage(bank=1, voltage=BankVoltage.V5P0)
            lw.write_bank_voltage(bank=2, voltage=BankVoltage.V5P0)
            lw.write_bank_voltage(bank=3, voltage=BankVoltage.V5P0)
            ch1.enable_output(True)
            ch2.enable_output(True)
        
            time.sleep(1)
        
            uart = lw.uart(instance_num=0,tx_pin=32, rx_pin=33)

            # Example of calling the new logging functions for a "BIT" test
            #bypass_error_and_log(uart, bit_log_file, "1\n")
            #read_until_end_and_log(uart, bit_log_file, "1\n", "BIT")
            
            # Example of calling the new logging functions for an "ATP" test
            bypass_error_and_log(uart, atp_log_file, "3\n")
            read_until_end_and_log(uart, atp_log_file, "3\n", "ATP")

            ch1.enable_output(False)
            ch2.enable_output(False)

    except Exception as e:
        print(f"An error occurred: {e}")
        print("Please ensure your LogicWeave device is connected and drivers are installed.")