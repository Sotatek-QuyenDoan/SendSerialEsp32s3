import serial
import time
import os
import wave
import struct

SERIAL_PORT = 'COM7'         # Thay bằng cổng COM của bạn
BAUDRATE = 921600
TIMEOUT = 5                  # Thời gian chờ ESP32 xác nhận (giây)

# # In hex một phần data (giữ lại cho debug)
# def print_block_hex(data, maxlen=32):
#     hexstr = data.hex().upper()
#     for i in range(0, min(len(hexstr), maxlen*2), 2):
#         print(hexstr[i:i+2], end='')
#         if (i//2+1) % 32 == 0:
#             print()
#     if len(hexstr) > maxlen*2:
#         print("...")
#     else:
#         print()

def send_file_streaming(ser, wav_path):
    # Đọc file WAV
    with wave.open(wav_path, 'rb') as wav:
        n_channels, sampwidth, framerate, n_frames, comptype, compname = wav.getparams()
        data = wav.readframes(n_frames)
    total_bytes = len(data)
    print(f"Sending file: {wav_path} ({total_bytes} bytes, streaming, UART speed: {BAUDRATE}bps)")

    # Gửi 4 byte đầu là tổng số byte (little endian)
    ser.write(struct.pack('<I', total_bytes))
    print(f"[SEND HEADER] Tổng số byte: {total_bytes}")

    # Gửi data liên tục, không sleep, không phụ thuộc sample rate
    sent = 0
    chunk_size = 1024  # Gửi từng chunk lớn để tối ưu tốc độ
    send_start = time.time()
    while sent < total_bytes:
        chunk = data[sent:sent+chunk_size]
        ser.write(chunk)
        sent += len(chunk)
        if sent % (chunk_size * 10) == 0 or sent == total_bytes:
            print(f"[SENT] {sent}/{total_bytes} bytes")
    send_end = time.time()
    print(f"\nĐã gửi xong toàn bộ data, chờ ESP32 xác nhận...")

    # Nhận log xác nhận từ ESP32
    ser.timeout = 0.5
    wait_start = time.time()
    buffer = b""
    while time.time() - wait_start < TIMEOUT:
        if ser.in_waiting:
            buffer += ser.read(ser.in_waiting)
            if b"ESP32: Received all data" in buffer:
                print("[ESP32 LOG]", buffer.decode(errors='ignore').strip())
                break
        time.sleep(0.05)
    else:
        print("[TIMEOUT] Không nhận được xác nhận từ ESP32!")
    wait_end = time.time()

    print(f"Thời gian gửi file: {send_end - send_start:.3f} giây")
    print(f"Tổng thời gian (gửi + chờ xác nhận): {wait_end - send_start:.3f} giây")

if __name__ == "__main__":
    with serial.Serial(SERIAL_PORT, BAUDRATE, timeout=0.1) as ser:
        wav_path = input("Nhập đường dẫn file WAV cần gửi: ").strip()
        if not os.path.isfile(wav_path):
            print("File không tồn tại!")
        else:
            send_file_streaming(ser, wav_path)
        print("Done.")
