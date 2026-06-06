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


The fixed strings are written to the screen by the @WriteText function, which also handles localization and
some sort of fixup that I haven't figured out yet:

```
; Write a localized string to the screen
; `A` String id
.func WriteText:
7a4f  c918    CMP #$18                   ; If id < 24
7a51  9003    BCC write_localized_string ; then this is a localized string (display strings start at 24 == "X")
7a53  0a      ASL                        ; multiply id by two since we need a word address
7a54  d048    BNE write_unlocalized_string ;
.label write_localized_string:
7a56  48      PHA                        ; Cache the string id
7a57  a621    LDX language_setting       ; Read the current language (set by dip switches)
7a59  f010    BEQ write_language_zero    ; If language is zero (english) handle it specially
7a5b  ca      DEX                        ; Starting index into the localized string table
7a5c  7da15f  ADC localized_language_offset[0],X ; based on the language setting - 1
7a5f  aa      TAX                        ; Strings in the localized table
7a60  bda45f  LDA localized_string_offset[0],X ; ???
7a63  a200    LDX #$00                   ;
7a65  0a      ASL                        ;
7a66  900f    BCC L7a77                  ;
7a68  ca      DEX                        ;
7a69  b00c    BCS L7a77                  ;
.label write_language_zero:
7a6b  e908    SBC #$08                   ; There's some fixups, not sure what is going on here
7a6d  c90c    CMP #$0c                   ;
7a6f  b013    BCS L7a84                  ;
7a71  aa      TAX                        ;
7a72  bd6d69  LDA string_table_fixup_something_else,X ;
7a75  a200    LDX #$00                   ;
.label L7a77:
7a77  18      CLC                        ;
7a78  a002    LDY #$02                   ;
7a7a  712f    ADC (VecRamPtr_copy2),Y    ; Maybe special characters? I'm really not sure yet.
7a7c  912f    STA (VecRamPtr_copy2),Y    ;
7a7e  8a      TXA                        ;
7a7f  c8      INY                        ;
7a80  712f    ADC (VecRamPtr_copy2),Y    ;
7a82  912f    STA (VecRamPtr_copy2),Y    ;
.label L7a84:
7a84  68      PLA                        ; Restore original string id from the stack
7a85  0a      ASL                        ; Double it to get a word offset
7a86  c930    CMP #$30                   ; Check if the original id is >= 24
7a88  b014    BCS write_unlocalized_string ; this is a non-localized string (24 == "X")
7a8a  a621    LDX language_setting       ; If the language is zero
7a8c  f010    BEQ write_unlocalized_string ; then this is also un-localized
7a8e  ca      DEX                        ; Get the starting
7a8f  18      CLC                        ; string id in the big localized string table
7a90  7d0058  ADC string_table_language_offset[0],X ; for this string language and add it to the string id
7a93  aa      TAX                        ; Read `A:Y` = string_table_localized[string_id + string_table_lang_offset[language-1]]
7a94  bc0458  LDY string_table_localized[0],X ; low byte
7a97  bd0558  LDA string_table_localized_high[0],X ; and high bytes fo the pointer
.label call_draw_string:
7a9a  aa      TAX                        ; Convert the string pointer from `A:Y` into `X:Y`
7a9b  4cf279  JMP DrawString             ; and tall call @DrawString
.label write_unlocalized_string:
7a9e  aa      TAX                        ; Index into the english string table
7a9f  bc2b69  LDY string_table[0],X      ; and read the low
7aa2  bd2c69  LDA string_table_high[0],X ; and high bytes into `A:Y`
7aa5  d0f3    BNE call_draw_string       ;

; Shared return instruction for a few functions
.func rts_7aa7:
7aa7  60      RTS                        ; Return to caller
```


### English strings

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

### Localized strings

```
.byte 5fa1 localized_language_offset 3 ; String id mapping for each language
.byte 5fa4 localized_string_offset 93 ; Index into the big string table for localized strings
```

```
.byte 5800 string_table_language_offset 3 ; Amount to add to string IDs to get the localized version for each language
.ptr 5804 string_table_localized 72 ; Localized strings
```


```
.byte 5894 str_APPUYER_SUR_START 17 ; 0 "APPUYER SUR START"
.byte 58c6 str_CARBURANT_DIMINUE 17 ; 1 "CARBURANT DIMINUE"
.byte 58fa str_PLUS_DE_CARBURANT 17 ; 2 "PLUS DE CARBURANT"
.byte 592e str_PERDUES 7 ; 3 "PERDUES"
.byte 5948 str_INTRODUIRE_LES_PIECES 21 ; 4 "INTRODUIRE LES PIECES"
.byte 5979 str_PAR_PIECE 9 ; 5 "PAR PIECE"
.byte 599c str_RESERVOIR_AUXILIAIRE_DE_CARBURANT_DETRUIT 41 ; 6 "RESERVOIR AUXILIAIRE DE CARBURANT DETRUIT"
.byte 5a10 str_FELICITATIONS 13 ; 7 "FELICITATIONS"
.byte 5a36 str_VOUS_AVEZ_ATTERRI_DIFFICILEMENT 31 ; 8 "VOUS AVEZ ATTERRI DIFFICILEMENT"
.byte 5a86 str_SPLENDIDE_ATTERRISSAGE 22 ; 9 "SPLENDIDE ATTERRISSAGE"
.byte 5ad2 str_LE_EAGLE_A_ATTERRI 18 ; 10 "LE EAGLE A ATTERRI"
.byte 5b0c str_LE_COLUMBIA_A_ATTERRI 21 ; 11 "LE COLUMBIA A ATTERRI"
.byte 5b4e str_VOUS_AVEZ_ATTERRI 17 ; 12 "VOUS AVEZ ATTERRI"
.byte 5b82 str_LE_SUPPORT_DE_SAUVETAGE_EST_PARTI 33 ; 13 "LE SUPPORT DE SAUVETAGE EST PARTI"
.byte 5bea str_VOTRE_VOYAGE_EST_SANS_RETOUR 28 ; 14 "VOTRE VOYAGE EST SANS RETOUR"
.byte 5c36 str_PERDU_SANS_ESPOIR 17 ; 15 "PERDU SANS ESPOIR"
.byte 5c8d str_SYSTEME_DE_COMMUNICATION_DETRUIT 32 ; 16 "SYSTEME DE COMMUNICATION DETRUIT"
.byte 5cec str_VOUS_AVEZ_CREE_UN_CRATERE_DE_DEUX_KILOMETRES 44 ; 18 "VOUS AVEZ CREE UN CRATERE DE DEUX KILOMETRES"
.byte 5d6a str_VOUS_AVEZ_UN_CRASH 18 ; 19 "VOUS AVEZ UN CRASH"
.byte 5daa str_IL_NEY_A_PAS_DE_SURVIVANTS 26 ; 20 "IL NEY A PAS DE SURVIVANTS"
.byte 5e02 str_CHOIX_DU_JEU 12 ; 22 "CHOIX DU JEU"
.byte 5e23 str__UNITES_DE_CARBURANT_ 21 ; 23 " UNITES DE CARBURANT "
.byte 58a5 str_PULSAR_START 12 ; 24 "PULSAR START"
.byte 58d7 str_POCO_COMBUSTIBLE 16 ; 25 "POCO COMBUSTIBLE"
.byte 590b str_SIN_COMBUSTIBLE 15 ; 26 "SIN COMBUSTIBLE"
.byte 5935 str_PERDIDAS 8 ; 27 "PERDIDAS"
.byte 595d str_INSERTE_FICHAS 14 ; 28 "INSERTE FICHAS"
.byte 5982 str_POR_FICHA 9 ; 29 "POR FICHA"
.byte 59c5 str_TANQUES_AUXILIARES_DE_COMBUSTIBLE_DESTRUIDOS 44 ; 30 "TANQUES AUXILIARES DE COMBUSTIBLE DESTRUIDOS"
.byte 5a1d str_FELICITACIONES 14 ; 31 "FELICITACIONES"
.byte 5a55 str_USTED_ALUNIZO_VIOLENTAMENTE 27 ; 32 "USTED ALUNIZO VIOLENTAMENTE"
.byte 5a9c str_FUE_UN_GRAN_ALUNIZAJE 21 ; 33 "FUE UN GRAN ALUNIZAJE"
.byte 5ae4 str_EL_AGUILA_HA_ALUNIZADO 22 ; 34 "EL AGUILA HA ALUNIZADO"
.byte 5b21 str_EL_COLUMBIA_HA_ALUNIZADO 24 ; 35 "EL COLUMBIA HA ALUNIZADO"
.byte 5b5f str_USTED_HA_ALUNIZADO 18 ; 36 "USTED HA ALUNIZADO"
.byte 5ba3 str_EQUIPO_DE_SUPERVIVENCIA_DESTRUIDO 33 ; 37 "EQUIPO DE SUPERVIVENCIA DESTRUIDO"
.byte 5c06 str_SU_VIAJE_ES_DE_IDA_SOLAMENTE 28 ; 38 "SU VIAJE ES DE IDA SOLAMENTE"
.byte 5c47 str_LAMENTABLEMENTE_USTED_NO_PUEDE_VOLVER 37 ; 39 "LAMENTABLEMENTE USTED NO PUEDE VOLVER"
.byte 5cad str_SISTEMA_DE_COMUNICACION_DESTRUIDO 33 ; 40 "SISTEMA DE COMUNICACION DESTRUIDO"
.byte 5d18 str_USTED_CREO_UN_CRATER_DE_2_KILOMETROS 36 ; 42 "USTED CREO UN CRATER DE 2 KILOMETROS"
.byte 5d7c str_DEMOLER 7 ; 43 "DEMOLER"
.byte 5dc4 str_NO_HUBO_SOBREVIVIENTES 22 ; 44 "NO HUBO SOBREVIVIENTES"
.byte 5df4 str__PUNTOS 7 ; 45 " PUNTOS"
.byte 5e0e str_ELEGIR_JUEGO 12 ; 46 "ELEGIR JUEGO"
.byte 5e38 str__UNIDADES_DE_COMBUSTIBLE_ 25 ; 47 " UNIDADES DE COMBUSTIBLE "
.byte 58b1 str_STARTKNOEPFE_DRUECKEN 21 ; 48 "STARTKNOEPFE DRUECKEN"
.byte 58e7 str_TREIBSTOFF_GEHT_AUS 19 ; 49 "TREIBSTOFF GEHT AUS"
.byte 591a str_TREIBSTOFFTANKS_LEER 20 ; 50 "TREIBSTOFFTANKS LEER"
.byte 593d str_TEILVERLUST 11 ; 51 "TEILVERLUST"
.byte 596b str_GELD_AUSWERFEN 14 ; 52 "GELD AUSWERFEN"
.byte 598b str_ZUKAUF_PRO_MUENZE 17 ; 53 "ZUKAUF PRO MUENZE"
.byte 59f1 str_ZUSATZTREIBSTOFFTANKS_ZERSTOERT 31 ; 54 "ZUSATZTREIBSTOFFTANKS ZERSTOERT"
.byte 5a2b str_GRATULATION 11 ; 55 "GRATULATION"
.byte 5a70 str_SIE_SIND_HART_GELANDET 22 ; 56 "SIE SIND HART GELANDET"
.byte 5ab1 str_DIES_WAR_EINE_GROSSARTIGE_LANDUNG 33 ; 57 "DIES WAR EINE GROSSARTIGE LANDUNG"
.byte 5afa str_EAGLE_IST_GELANDET 18 ; 58 "EAGLE IST GELANDET"
.byte 5b39 str_COLUMBIA_IST_GELANDET 21 ; 59 "COLUMBIA IST GELANDET"
.byte 5b71 str_SIE_SIND_GELANDET 17 ; 60 "SIE SIND GELANDET"
.byte 5bc4 str_LEBENSRETTUNGSSYSTEME_SIND_AUSGEFALLEN 38 ; 61 "LEBENSRETTUNGSSYSTEME SIND AUSGEFALLEN"
.byte 5c22 str_REISE_OHNE_RUECKKEHR 20 ; 62 "REISE OHNE RUECKKEHR"
.byte 5c6c str_KEIN_RUECKSTART_ZUR_ERDE_MOEGLICH 33 ; 63 "KEIN RUECKSTART ZUR ERDE MOEGLICH"
.byte 5cce str_KOMMUNIKATIONSSYSTEM_ZERSTOERT 30 ; 64 "KOMMUNIKATIONSSYSTEM ZERSTOERT"
.byte 5d3c str_SIE_HABEN_EINEN_2_KILOMETER_KRATER_AUFGERISSEN 46 ; 66 "SIE HABEN EINEN 2 KILOMETER KRATER AUFGERISSEN"
.byte 5d83 str_50_000_000_MARK_SIND_IN_DIE_LUFT_GEJAGT 39 ; 67 "50 000 000 MARK SIND IN DIE LUFT GEJAGT"
.byte 5dda str_KEINE_UEBERLEBENDEN 19 ; 68 "KEINE UEBERLEBENDEN"
.byte 5dfb str__PUNKTE 7 ; 69 " PUNKTE"
.byte 5e1a str_SPIELWAHL 9 ; 70 "SPIELWAHL"
.byte 5e51 str__TREIBSTOFF_ 12 ; 71 " TREIBSTOFF "
```
