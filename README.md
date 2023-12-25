# MIPS Instruction Inserter for RTC
A python script that takes an input text file containing a "jump-from" address, an "insert" address where code is put at, and an instruction section with various available commands to perform (including jumping to another address and coming back as safely as possible), then generates a blast layer file to load in [RTC](https://redscientist.com/RTC)

## Purpose
The general purpose of this script is to make it easy to add to a corruption a trigger on a specific action or event. For example, instead of activating a corruption on a certain frame, you can have it activate when the character swings his sword.

One command you can use, "corrupt:filename.bl", converts a corruption from RTC into code that activates this corruption when the "jump-to" address is executed. For most people, I expect this command is all you will need.

Additionally, there are various commands that make it easier to add MIPS assembly code, it's kind of a very basic compiler.

The instruction section in the input file is designed so you can paste a line from a bizhawk trace log and it will load all registers from that line and then jump to the address.

## Showcase
https://youtu.be/6Z7kUmatDio

https://youtu.be/_L3qaoim4Wk

## Usage
- You will need python, any python 3 version should work.
- Edit input.txt, all options are explained inside.
- Run "create jumper.py", a .bat is included for windows.
- Load or import the output .bl file in RTC Blast Editor.

## Finding addresses
The bulk of the work you need to do to use this script is finding the right address you need to trigger things on a specific action. This might seem daunting if you've never looked at the hex editor or debugging tools, but it's quite simple once you've tried it, especially if you have corruptions related to the action, as these corruptions might already contain a useable address.

First, for the address to insert code at, all that is required is enough space, any location will do. This is very easy to find on most games (possibly more difficult on PSX as the RAM is smaller); scroll through hex editor until you find a bunch of 0. If you want your corruption to work across multiple areas and such, make sure that memory area stays empty throughout (changing lifetime to 0 on all of the custom code is probably not a good idea). Required space depends on backup type and instructions, at minimum 7 rows.

Second, the jump-from address. The main thing you need to know is how to test when an address is being executed. If you have a related corruption unit, simply open the debugger on the emulator and add a breakpoint for that address, with "execute" type. Then see if the breakpoint is triggered (emulation stops) every frame, only when the related action happens, or never.
- If breakpoint triggers every frame: the address is from either a common function used by many things, or the function can be related to the action but is entered every frame and exits out if the conditions are not right, in which case an address slightly after it might be good.
- If breakpoint triggers only on the related action: you have a good address. Additionally, for the address to be useable, it needs to either be replaceable by a NOP (all 0s) without critical effect, or the instruction on it and the next address need to not be jump or branch, so that they can be moved to the custom code section. Set the "Move Code" option in input.txt accordingly.
- If breakpoint never triggers: this can mean either the address is on a delay slot which the emulator does not detect properly (try a breakpoint on the previous address by lowering the address number by 4), or the address is not code but a stored value, in which case you can change the breakpoint type to "read" to possibly find a code address related to the action that reads this value.

If you end up with a dead end with the breakpoint, or you don't have a related corruption, you can usually easily find stored value addresses related to the action by using RAM search tool on bizhawk; search for values that are different when paused on the start of the action (on PCSX2 you could probably use cheat engine instead). You can then set a "read" or "write" breakpoint on found addresses.

Lastly, finding an address to jump to can be quite a bit more tricky, as you usually want to find a specific address, either the start of a function or after a condition. In general, you start by finding an address the same way as jump-from, then after stopping at the breakpoint of this address, rewind a frame or two, then output a trace log to file (set max file size to 10mb) until the breakpoint is hit again, then search the files for the address, and figure the code out from there. On PCSX2 there is no logging as far as I can see, however the debugger is good enough to figure the function out directly from there. I would need to make a more in-depth tutorial for more instructions on this; you also usually need to find values in memory that the function is expecting and manually put them in before jumping, debug why it inevitably crashes, make sure the stack pointer is far enough away from before, makes sure return address is safe, etc. You can consider this jump instruction as being for advanced users.

## About registers
Most of everything in this script deals with registers, which are a select few variables directly inside the CPU. As of now, it only deals with the 32 regular MIPS registers, Float point registers and other special registers are not implemented. 

If the backup option is selected, the registers are stored at the start of the custom code location and restored when returning (a few are backed up regardless, specifically AT,SP,RA). You can view the list of registers on the emulator's debugger.

IMPORTANT: Do not use the register AT in your instructions, as it is used for executing some of these instructions, the same way it is used on normal assemblers (register name is "assembler temporary"). Also avoid using k0 or k1 as these can get modified in the middle of your code.

At the start of the instruction section, the register RA contains the address where custom code is inserted at, same as in input file. Useful to have instead of specifying the address, especially if you want to reuse code for different games, but make sure you use it before a jump as it will change at that point.

## Commands you can use in the instruction section:
Keep in mind that these commands generate code in the order that they are listed.

corrupt:"file name or path.bl" -- reads a saved corruption file from RTC and converts it to code that triggers this corruption when the code runs (execute frame, lifetime and loop values are ignored. I could implement these, with some caveats, if there's demand for it)

code:00000000 -- inserts code here as is, must be 8 characters long

### Value assignments and addition
In all assignment and memory instructions, you can think of the ":" character as "="

T1:34 -- sets register T1 to HEX value 34, if length is more than 8, only last 8 characters are used

T1:+34 -- sets register T1 to DECIMAL value 34 (T1:-34 is decimal -34, which will end up as HEX FFFFFFDE)

T1:T2+10 -- sets register T1 to T2 + 10(decimal), substraction is also available, but no multiplication or division, you'll have to look those up and add them through "code:" command

### Memory store/load
SP:803AC000 -- SP is the stack pointer register, used in all memory store/load instructions below -- IMPORTANT: these addresses need to be the full 8 characters starting with 8 (unless on ps2)

SP0:100 -- writes the HEX value 100 to the memory address currently in SP, replacing the entire word length (in this case, the address would become 00000100)

SP4:T1 -- writes the value in register T1 to the SP address + offset 4, which means the next "word" address (8 hex characters) as the offset is in bytes (2 hex characters)

SPH6:0 -- H for halfword (4 hex characters), this writes 0000 to the second half of the address after SP

T2:SPB3 -- B for Byte, this loads the 3rd byte of SP address into register T2 (if address contains 12345678, T2 would become 00000056)

SP0:SP0+1 -- loads the value in SP address, adds 1, then stores it to the same address, similar to a tilt unit type in RTC, useful to create a counter to check how many times the custom code is executed

### Branching
exit: -- unconditional exit out of custom code, restoring backed-up registers if backup is on then returning to jump-from address (an exit is always at the end of instructions, this command is to add another one somewhere else)

branch_a: -- does not add any code, sets a location for the script with the name "a" (underscores are optional, use them wherever for clarity)

branch:a -- unconditional branch to location "a" (delay slots are taken care of by the script)

branch_if_T1=0:a -- branch to location "a" if condition is true. You can use =,!,<,> for conditional operators, first value must be register, second can be register or number (decimal by default, use 0x for hex)

exit_if_T1<T2: -- exit if condition is true

### Jumping
80123450: or 123450: -- adds a jump to specified address, not where this is written but before the next jump or "after:" command, or at the end of instructions

after: -- inserts the preceding jump instruction here, indicating that the following instructions are after the jump

## About backup type
You'll usually only want to turn on the backup option if you have a jump command. If you need one or two variables in your code, you could also back them up manually, or assume modifying a register or two won't cause any issue. If space is no issue and you want to be safe, turn on backup option.

There are two backup types provided: compact and stable.

Stable backup writes store/load instructions for each register.

Compact backup uses a loop with self-modifying code to change the register that is stored or restored. This is very unusual code, and I had to do a lot to make this work across all consoles. It seems stable now, but still only use this if you lack the space.

## About console differences
N64: 
- Pure interpreter is strongly recommended. Other interpreters have very strong code instruction caching, which breaks compact backup and more importantly does not allow most code corruptions to activate during gameplay, rendering a lot of what you can do with this useless. 
- Debugger on N64 core is useable, but trace logs are required to really figure things out as precise debugging is not available.
- Registers are 64 bits but the other half is barely ever used. This script only deals with the first 32 bits. There are also additional registers on a separate processor used for float point operations, which are also not dealt with. I've not had to so far, possibly they are rarely essential.
- Uses Big Endian (which means it needs to be off on RTC if the value is in the correct order? I still don't get endianness.)
   
PSX: 
- S8 register (second to last) is called FP on this system. This script only accepts S8, so you will need to use S8 if you want to do something with this register.
- Compact backup is less compact as it requires additional code to circumvent instruction caching (caching is not as strong as N64 normal interpreter, does not prevent activating corruptions). 
- Bizhawk debugger with PSX core seems to barely work, I recommend using Duckstation to find addresses. (you CAN do the essentials on bizhawk like finding if an address is triggered and output a trace log, but the debugger does not even display the correct information for breakpoints)
- Registers are 32 bits.
- In addition to branch/jump delay slots, PSX has load delay slots, meaning the instruction after a load should not use the register being written to, as the load has not yet completed. I think I've dealt with all pertinent cases in the script, but keep that in mind if you add custom code.
- Uses Little Endian (Big Endian is checked on RTC)
   
PS2:
- S8 register (second to last) is called FP on this system. This script only accepts S8, so you will need to use S8 if you want to do something with this register.
- PCSX2 lacks much of the tools available on bizhawk, but has a pretty good debugger with precise interruption and step in/out/over.
- Registers are 128 bits, not sure how frequently more than 32 bits are used, I've not done much testing on PS2.
- Addresses starting with "8" are technically invalid on this system, but they seem to still work fine, at least on PCSX2.
- Uses Little Endian (Big Endian is checked on RTC)

## Useful MIPS ressources
Hex <-> Instruction Converter

https://www.eg.bucknell.edu/~csci320/mips_web/


Instruction set (paste the instruction name, such as "addi", by itself on the converter site above for more information about that instruction)

https://www.dsi.unive.it/~gasparetto/materials/MIPS_Instruction_Set.pdf


I've included a text file with addresses and bits of code I collected for N64 Majora Mask, you can use it to try out the script and help you figure out how to use it.
