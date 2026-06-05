## Strings

Text strings are drawn as a sequence of DVG subroutine calls, each character is a DVG `JSRL` subroutine call
copied from the @CharPtrTbl to the vector generator RAM.  The strings are stored not in ASCII, but with
the offsets into the font table of the character subroutine call, and the last character in the string
has the high bit set as a terminator.

```
.word 2b draw_string_ptr ; Pointer to character in a string being copied to vector ram
```

```
; DrawString
; `X:Y` Pointer to the string to write, terminated with 0x80 on the last character
; Copies the font subroutines to @VecRamPtr
; Sets @draw_string_ptr to point to the end of the string
.func DrawString:
79f2  862c    STX draw_string_ptr_high   ; Store the pointer high
79f4  842b    STY draw_string_ptr        ; and low bytes
79f6  a900    LDA #$00                   ; for i = 0 ... strlen * 2
.label copy_next_vec_instruction:
79f8  4a      LSR                        ; halve i since we're copying 16-bit `JSRL` vector subroutine
79f9  a8      TAY                        ; calls for each letter and it is going up by two each byte
79fa  b12b    LDA (draw_string_ptr),Y    ; Read low byte from the string
79fc  8539    STA GenByte_0039           ; Cache it in gen byte
79fe  297f    AND #$7f                   ; Strings are terminated by setting the high bit
7a00  aa      TAX                        ; so strip the high bit from the letter
7a01  98      TYA                        ; move y back into a
7a02  0a      ASL                        ; and double it back to by index by words
7a03  a8      TAY                        ; and back into y (what a dance)
7a04  bda257  LDA CharPtrTbl[0],X        ; Index into the font table to get the low byte
7a07  9127    STA (VecRamPtr),Y          ; and store it in the vector ram ptr
7a09  c8      INY                        ; next byte...
7a0a  bda357  LDA CharPtrTbl_high[0],X   ; store the high byte of the font into the vector ram ptr
7a0d  9127    STA (VecRamPtr),Y          ; indexed by y
7a0f  c8      INY                        ; and increment y again since we moved two bytes
7a10  98      TYA                        ; and back into a
7a11  2439    BIT GenByte_0039           ; Test the cached version of the letter
7a13  10e3    BPL copy_next_vec_instruction ; If positive, keep copying
7a15  18      CLC                        ; Clear carry
7a16  6527    ADC VecRamPtr              ; Add number of bytes written to vector ram
7a18  8527    STA VecRamPtr              ; to the @VecRamPtr
7a1a  9002    BCC increment_char_ptr     ; Did the low byte overflow?
7a1c  e628    INC VecRamPtr_high         ; if so increment the high byte as well
.label increment_char_ptr:
7a1e  98      TYA                        ; Copy number of bytes copied to vector ram back to A
7a1f  4a      LSR                        ; Divide it by two to get the number of characters in the string
7a20  652b    ADC draw_string_ptr        ; Increase the character pointer
7a22  852b    STA draw_string_ptr        ; so it points to the end of the string
7a24  9002    BCC draw_string_return     ; did the low byte overflow?
7a26  e62c    INC draw_string_ptr_high   ; if so increment the high byte as well
.label draw_string_return:
7a28  60      RTS                        ; return to the caller
```

There are 33 strings in the game and they are all indexed by number. For English the table has the pointers,
note that string number 17 is an index into string 16 to reuse the word `DESTROYED`.

```
.ptr 692b string_table 33 ; Pointers to the English strings
.byte 69ab str_PUSH_START 10 ; 0 "PUSH START"
.byte 6979 str_LOW_ON_FUEL 11 ; 1 "LOW ON FUEL"
.byte 6984 str_OUT_OF_FUEL 11 ; 2 "OUT OF FUEL"
.byte 698f str_LOST 4 ; 3 "LOST"
.byte 699f str_INSERT_COINS 12 ; 4 "INSERT COINS"
.byte 69dd str_PER_COIN 8 ; 5 "PER COIN"
.byte 69e6 str_AUXILIARY_FUEL_TANKS_DESTROYED 30 ; 6 "AUXILIARY FUEL TANKS DESTROYED"
.byte 6a04 str_CONGRATULATIONS 15 ; 7 "CONGRATULATIONS"
.byte 6a13 str_YOU_LANDED_HARD 15 ; 8 "YOU LANDED HARD"
.byte 6a22 str_THAT_WAS_A_GREAT_LANDING 24 ; 9 "THAT WAS A GREAT LANDING"
.byte 6a3a str_THE_EAGLE_HAS_LANDED 20 ; 10 "THE EAGLE HAS LANDED"
.byte 6a4e str_THE_COLUMBIA_HAS_LANDED 23 ; 11 "THE COLUMBIA HAS LANDED"
.byte 6a65 str_YOU_HAVE_LANDED 15 ; 12 "YOU HAVE LANDED"
.byte 6a74 str_LIFE_SUPPORT_IS_GONE 20 ; 13 "LIFE SUPPORT IS GONE"
.byte 6a88 str_YOUR_TRIP_IS_ONE_WAY 20 ; 14 "YOUR TRIP IS ONE WAY"
.byte 6a9c str_YOU_ARE_HOPELESSLY_MAROONED 27 ; 15 "YOU ARE HOPELESSLY MAROONED"
.byte 6ab7 str_COMMUNICATION_SYSTEM_DESTROYED 30 ; 16 "COMMUNICATION SYSTEM DESTROYED"
.byte 6ad5 str_YOU_CREATED_A_TWO_MILE_CRATER 29 ; 18 "YOU CREATED A TWO MILE CRATER"
.byte 6af2 str_YOU_JUST_DESTROYED_A_100_MEGABUCK_LANDER 40 ; 19 "YOU JUST DESTROYED A 100 MEGABUCK LANDER"
.byte 6b1a str_THERE_WERE_NO_SURVIVORS 23 ; 20 "THERE WERE NO SURVIVORS"
.byte 69c2 str__POINTS 7 ; 21 " POINTS"
.byte 69b5 str_SELECT_OPTION 13 ; 22 "SELECT OPTION"
.byte 6993 str__FUEL_UNITS_ 12 ; 23 " FUEL UNITS "
.byte 69e5 str_X 1 ; 24 "X"
.byte 69c9 str_450 3 ; 25 "450"
.byte 69cc str_600 3 ; 26 "600"
.byte 69cf str_750 3 ; 27 "750"
.byte 69d2 str_900 3 ; 28 "900"
.byte 64ff str_1100 4 ; 29 "1100"
.byte 6503 str_1300 4 ; 30 "1300"
.byte 69d5 str_1550 4 ; 31 "1550"
.byte 69d9 str_1800 4 ; 32 "1800"
```


