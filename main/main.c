#include <stdio.h>
#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/uart.h"

#define UART_NUM        UART_NUM_0
#define UART_TX_PIN     43
#define UART_RX_PIN     44
#define BAUD_RATE       921600
#define RX_BUF_SIZE     256
#define HEADER_SIZE     4 // 4 byte đầu là tổng số byte data

static void uart_receive_streaming_task(void *arg)
{
    while (1){
    uint8_t header[HEADER_SIZE];
    int received = 0;
    // Nhận 4 byte đầu là tổng số byte data
    while (received < HEADER_SIZE) {
        int len = uart_read_bytes(UART_NUM, header + received, HEADER_SIZE - received, pdMS_TO_TICKS(100));
        if (len > 0) received += len;
    }
    uint32_t total_bytes = 0;
    memcpy(&total_bytes, header, 4);

    printf("Expecting %ld bytes\n", total_bytes);

    uint8_t buf[1024];
    uint32_t received_bytes = 0;
    while (received_bytes < total_bytes) {
        int to_read = (total_bytes - received_bytes) > sizeof(buf) ? sizeof(buf) : (total_bytes - received_bytes);
        int len = uart_read_bytes(UART_NUM, buf, to_read, pdMS_TO_TICKS(100));
        if (len > 0) {
            // Xử lý buf[0..len-1] ở đây nếu cần (ghi flash, phát DAC, ...)
            received_bytes += len;
        }
    }
    // Gửi log báo đã nhận xong
    const char *done_msg = "ESP32: Received all data\n";
    uart_write_bytes(UART_NUM, done_msg, strlen(done_msg));
    printf("Đã nhận đủ %ld bytes, đã gửi log xác nhận về PC.\n", total_bytes);
    //vTaskDelete(NULL);
    }
}

void app_main(void)
{
    uart_config_t uart_config = {
        .baud_rate = BAUD_RATE,
        .data_bits = UART_DATA_8_BITS,
        .parity    = UART_PARITY_DISABLE,
        .stop_bits = UART_STOP_BITS_1,
        .flow_ctrl = UART_HW_FLOWCTRL_DISABLE
    };
    uart_param_config(UART_NUM, &uart_config);
    uart_set_pin(UART_NUM, UART_TX_PIN, UART_RX_PIN, UART_PIN_NO_CHANGE, UART_PIN_NO_CHANGE);
    uart_driver_install(UART_NUM, RX_BUF_SIZE * 2, 0, 0, NULL, 0);

    xTaskCreate(uart_receive_streaming_task, "uart_receive_streaming_task", 4096, NULL, 10, NULL);
}