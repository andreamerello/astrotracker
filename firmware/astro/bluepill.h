#ifndef BLUEPILL_H
#define BLUEPILL_H

typedef struct {
    const char *name; // this is used just as documentation
	uint32_t rcc;
	uint32_t port;
	uint32_t pin;
} pin_t;

static const pin_t PIN_A0  = {"A0",  .rcc = RCC_GPIOA, .port = GPIOA, .pin = GPIO0};
static const pin_t PIN_A1  = {"A1",  .rcc = RCC_GPIOA, .port = GPIOA, .pin = GPIO1};
static const pin_t PIN_A2  = {"A2",  .rcc = RCC_GPIOA, .port = GPIOA, .pin = GPIO2};
static const pin_t PIN_A3  = {"A3",  .rcc = RCC_GPIOA, .port = GPIOA, .pin = GPIO3};
static const pin_t PIN_A4  = {"A4",  .rcc = RCC_GPIOA, .port = GPIOA, .pin = GPIO4};
static const pin_t PIN_A5  = {"A5",  .rcc = RCC_GPIOA, .port = GPIOA, .pin = GPIO5};
static const pin_t PIN_A6  = {"A6",  .rcc = RCC_GPIOA, .port = GPIOA, .pin = GPIO6};
static const pin_t PIN_A7  = {"A7",  .rcc = RCC_GPIOA, .port = GPIOA, .pin = GPIO7};
static const pin_t PIN_A8  = {"A8",  .rcc = RCC_GPIOA, .port = GPIOA, .pin = GPIO8};
static const pin_t PIN_A9  = {"A9",  .rcc = RCC_GPIOA, .port = GPIOA, .pin = GPIO9};
static const pin_t PIN_A10 = {"A10", .rcc = RCC_GPIOA, .port = GPIOA, .pin = GPIO10};
static const pin_t PIN_A11 = {"A11", .rcc = RCC_GPIOA, .port = GPIOA, .pin = GPIO11};
static const pin_t PIN_A12 = {"A12", .rcc = RCC_GPIOA, .port = GPIOA, .pin = GPIO12};
static const pin_t PIN_A15 = {"A15", .rcc = RCC_GPIOA, .port = GPIOA, .pin = GPIO15};

// this is attached to the builtin led
static const pin_t PIN_C13 = {"C13", .rcc = RCC_GPIOC, .port = GPIOC, .pin = GPIO13};

#endif
