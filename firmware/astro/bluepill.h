#ifndef BLUEPILL_H
#define BLUEPILL_H

typedef struct {
    const char *name; // this is used just as documentation
	uint32_t rcc;
	uint32_t port;
	uint32_t pin;
} pin_t;


static const pin_t PIN_A9 = {
	.name = "A9",
	.port = GPIOA,
	.pin  = GPIO9,
	.rcc  = RCC_GPIOA,
};

// this is attached to the builtin led
static const pin_t PIN_PC13 = {
    .name = "PC13",
    .rcc  = RCC_GPIOC,
    .port = GPIOC,
    .pin  = GPIO13,
};

#endif
