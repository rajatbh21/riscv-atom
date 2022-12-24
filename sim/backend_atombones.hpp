#pragma once

#include "backend.hpp"
#include "build/verilated/VAtomBones.h"

#include <memory>

#define ATOMSIM_TARGETNAME  "atombones"
#define TARGET_ATOMBONES

class Memory;
class Vuart;

struct Backend_config
{
    uint32_t imem_offset    = 0x00010000;
    uint32_t imem_size_kb   = (64*1024);    // default: 64 MB
    
    uint32_t dmem_offset    = 0x20000000;
    uint32_t dmem_size_kb   = (64*1024);    // default: 64 MB

    std::string vuart_portname  = "";
    uint32_t vuart_baudrate     = 115200;
    bool enable_uart_dump       = false;
};


class Backend_atomsim: public Backend<VAtomBones>
{
public:
    /**
     * @brief Construct a new Backend object
     */
    Backend_atomsim(Atomsim * sim, Backend_config config);

    /**
	 * @brief Destroy the Backend object
	 */
	~Backend_atomsim();

    /**
     * @brief Get the Target Name
     * @return std::string 
     */
    std::string get_target_name() { return ATOMSIM_TARGETNAME; }

	/**
	 * @brief Service memory requests generated by iport and dport
	 */
    void service_mem_req();

	void refresh_state();

    void UART();

    int tick();
   
    void fetch(const uint32_t start_addr, uint8_t *buf, const uint32_t buf_sz);

    void store(const uint32_t start_addr, uint8_t *buf, const uint32_t buf_sz);

private:
    /**
     * @brief Backend configuration parameters
     */
    Backend_config config_;

    /**
     * @brief Map of pointers to memory devices
     */
    std::map<std::string, std::shared_ptr<Memory>> mem_;

    /**
	 * @brief Pointer to Vuart object
	 */
	Vuart *vuart_ = nullptr;

    /**
     * @brief Are we using vuart?
     */
    bool using_vuart_ = false;
};