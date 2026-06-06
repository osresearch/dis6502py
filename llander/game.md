# Start game

Original [A34573.1A](https://github.com/historicalsource/lunar-lander/blob/main/A34573.1A) source for the comments and variable names.


```
; Power on and main loop
.func start:
6001  201362  jsr ResetGameState         ; Initialize for attract
6004  a980    lda #$80                   ;
6006  855d    sta COLFLG                 ; Set VOLFLG for initial call to trans to setup lunar major scape

.label dogame:
6008  2497    bit CRDTFLG                ; CHK FOR CREDIT
600a  300f    bmi L601b                  ;
600c  a900    lda #$00                   ; NO CREDIT [ATTRACT]
600e  8522    sta GAMODE                 ;
6010  8597    sta CRDTFLG                ; CLR CREDIT
6012  245d    bit COLFLG                 ;
6014  104c    bpl MAINLP                 ;
6016  201362  jsr ResetGameState         ;
6019  d028    bne MJRCON                 ; ALWAYS
.label L601b:
601b  a522    lda GAMODE                 ; WHAT MODE WERE WE IN ?
601d  d021    bne PLYSTRT                ; BRANCH - WAS MOTION (GO TO PLAY MODE)
601f  201362  jsr ResetGameState         ; IN CASE OF FREE PLAY / ELSE - INITIALIZE FOR RTP / SET EASY GAME TYPE LED
6022  a9f0    lda #$f0                   ; LEAVE TOP NIBBLE
6024  a208    ldx #$08                   ; TURN ON LED (EASY)
6026  205f79  jsr io_lamps_set           ; SET LEDS &amp; ZP STAT
6029  a200    ldx #$00                   ;
602b  8623    stx PLYMOD                 ; GAME TYPE IS EASY
602d  86a4    stx SCORE                  ; CLR SCORE
602f  86a5    stx SCORE_high             ;
6031  a911    lda #$11                   ;
6033  8563    sta GRAVITY                ;
6035  a920    lda #$20                   ;
6037  a698    ldx C_OPT                  ; CHECK-FREE PLAY?
6039  d001    bne L603c                  ; BRANCH-NO
603b  4a      lsr                        ; ACC=^10
.label L603c:
603c  8522    sta GAMODE                 ; GAME MODE IS RTP
603e  d003    bne MJRCON                 ; ALWAYS
.label PLYSTRT:
6040  203562  jsr PLYINIT                ;
.label MJRCON:
6043  20a973  jsr TRANS                  ; CONSTRUCT MAJOR SCAPE
6046  a22c    ldx #$2c                   ; JSRL FOR ALPHAS
6048  a0ca    ldy #$ca                   ;
604a  a521    lda LANG                   ; CHK LANG #
604c  f004    beq L6052                  ;
604e  a2a0    ldx #$a0                   ; FOREIGN
6050  a0c3    ldy #$c3                   ; ALPHA DATA (at 4740 IN VG RAM)
.label L6052:
6052  a522    lda GAMODE                 ; CHECK RTP
6054  2920    and #$20                   ;
6056  f004    beq L605c                  ; BRANCH - NO RTP
6058  a200    ldx #$00                   ; ELSE - NO PLAYER DATA
605a  a0f0    ldy #$f0                   ; INSERT BLANK ALPHA
.label L605c:
605c  8e0040  stx VGRAM                  ;
605f  8c0140  sty VGRAM_high             ; ADD JSRL [PLAYER INFO] TO VG RAM
.label MAINLP:
6062  a240    ldx #$40                   ; ASSUME BUFFER 0 (4004 = VGRAM+4/100)
6064  a004    ldy #$04                   ; (VGRAM + 4) & 0xFF
6066  a586    lda FRAME                  ;
6068  4a      lsr                        ;
6069  9004    bcc L606f                  ; BRANCH - BUFFER 0
606b  a242    ldx #$42                   ; BUFFER 1 (4284 = VGRAM+284/100)
606d  a084    ldy #$84                   ; (VGRAM+284) & 0xFF
.label L606f:
606f  8628    stx RAMPTR_high            ;
6071  8427    sty RAMPTR                 ;
6073  a522    lda GAMODE                 ;
6075  2920    and #$20                   ;
6077  d02d    bne N_MOT1                 ; BRANCH - RTP
6079  209567  jsr MESDATA                ; NUMERICAL DATA
607c  203965  jsr SCAPE                  ; DISPLAY LANDSCAPE
607f  206765  jsr STARS                  ; DISPLAY STARFIELD
6082  20ad65  jsr MODULE                 ; DISPLAY MODULE
6085  a522    lda GAMODE                 ; CHECK FREE PLAY
6087  2910    and #$10                   ; BIT 4=FREE PLAY
6089  d01b    bne N_MOT1                 ; BRANCH-FREE PLAY
608b  2422    bit GAMODE                 ;
608d  101d    bpl N_MOT2                 ; BRANCH - NOT MOTION (ATTRACT OR PLAY)
608f  a562    lda M_CLFL                 ;
6091  290f    and #$0f                   ;
6093  f00b    beq MOTNA                  ; BRANCH - NOT CRASH
.label MOTION
6095  a529    lda PTRTMP                 ; ELSE - PTRTMP = LABS FOR MODULE
6097  8527    sta RAMPTR                 ; = ORIGIN OF EXPLOSION
6099  a52a    lda PTRTMP_high            ;
609b  8528    sta RAMPTR_high            ;
609d  209575  jsr BOOM                   ; DISPLAY EXPLOSION SEQUENCE
.label MOTNA:
60a0  20d668  jsr DSPMOT                 ; DISPLAY MOTION MESSAGES
60a3  4cce60  jmp BMREST                 ; REST VG BEAM at CNTR
.label N_MOT1:
60a6  207e68  jsr DSPRTP                 ; DISPLAY RTP MESSAGES
60a9  4cce60  jmp BMREST                 ;
.label N_MOT2:
60ac  209d66  jsr FLAME                  ;
60af  2422    bit GAMODE                 ;
60b1  5018    bvc L60cb                  ; BRANCH - NOT PLAY
60b3  a523    lda PLYMOD                 ;
60b5  d00b    bne L60c2                  ; BRANCH - NOT EASY PLAY MODE
60b7  a586    lda FRAME                  ;
60b9  290f    and #$0f                   ;
60bb  c908    cmp #$08                   ;
60bd  d003    bne L60c2                  ;
60bf  200965  jsr FRICTN                 ; EASY GAME PLAY = FRICTION
.label L60c2:
60c2  209e68  jsr STATUS                 ; DISPLAY FUEL STATUS [PLAY]
60c5  20ff67  jsr SITES                  ; FLASH BONUS SITES
60c8  4cce60  jmp BMREST                 ; REST VG BEAM at CNTR
.label L60cb:
60cb  209f79  jsr draw_insert_coin_screen ; DISPLAY ATTACH MESSAGES
.label BMREST:
60ce  a0de    ldy #$de                   ; VG BEAM at CNTR (REST & HALT) 0x4bde = FINI
60d0  a94b    lda #$4b                   ; FINI & 0xFF
60d2  a206    ldx #$06                   ;
60d4  20a67e  jsr VecCmd_memcpy          ;
60d7  ad0020  lda IO_in0                 ;
60da  2902    and #$02                   ; SELF TEST SWITCH, WAIT FOR WATCHDOG
.label L60dc:
60dc  f0fe    beq L60dc                  ; WAIT FOR END OF FRAME
60de  202d65  jsr dvg_wait_done          ;
60e1  a002    ldy #$02                   ;
60e3  a2f0    ldx #$f0                   ; ASSUME BUFFER 0 (4004)
60e5  a586    lda FRAME                  ;
60e7  4a      lsr                        ;
60e8  9004    bcc L60ee                  ; BRANCH - BUFFER 0
60ea  a2e1    ldx #$e1                   ; ELSE - BUFFER 1 (4284)
60ec  a042    ldy #$42                   ; 0x42e1 LOW BYTE OF JMPL
.label L60ee:
60ee  8e0340  stx D4003                  ; SET JMPL OR ALPH (BYTE 1) VGRAM + 3
60f1  8c0240  sty D4002                  ; SET BYTE 1 9FOR JMPL OR ALPH) VRAM + 2
60f4  8d0030  sta IO_DMAGO               ; START VG
60f7  e686    inc FRAME                  ;
60f9  a200    ldx #$00                   ; ASSUME NO SOUND
60fb  ad0020  lda IO_in0                 ; CHK SLAM
60fe  2904    and #$04                   ;
6100  d002    bne L6104                  ; BRANCH - NO SOUND
6102  a220    ldx #$20                   ; SND FOR SLAM
.label L6104:
6104  a91f    lda #$1f                   ; AND MASK
6106  205379  jsr io_audio_set           ; SET SND
6109  20e662  jsr coin_inserted          ; GIVE CRDT
610c  201464  jsr THRLVL                 ; THRUST LEVEL CALULCATION
610f  2422    bit GAMODE                 ;
6111  3037    bmi FRMEND                 ; BRANCH - MOTION
6113  501f    bvc L6134                  ; BRANCH - NOT PLAY
6115  20326b  jsr FRCMLT                 ; THRUST X,Y VECTORS
6118  203c63  jsr ROTSHIP                ; ROTATE SHIP
611b  20716b  jsr BURN                   ; BURN FUEL [THRUST]
611e  201b75  jsr DISPLY                 ; GENERATE PLAYER INFO (PLAY)
6121  a501    lda THRUST                 ; PLAY MODE THRUST SOUND
6123  c910    cmp #$10                   ; CHECK FOR ABORT
6125  d002    bne L6129                  ; BRANCH - NOT ABORT
6127  a90f    lda #$0f                   ; FOR ABORT MAX THRUST SOUND
.label L6129:
6129  4a      lsr                        ;
612a  0901    ora #$01                   ; MIN SOUND
612c  aa      tax                        ; SOUND LEVEL = THRUST/2 + 1
612d  a930    lda #$30                   ; AND MASK
612f  205379  jsr io_audio_set           ; SET NOISE
6132  d00d    bne L6141                  ; ALWAYS
.label L6134:
6134  a920    lda #$20                   ; NOSOUND - ATTRACT & RTP
6136  a200    ldx #$00                   ; JUST SLAM SW SOUND / DON'T SET ANY SOUNDS
6138  205379  jsr io_audio_set           ; SET NOISE
613b  a522    lda GAMODE                 ;
613d  2920    and #$20                   ;
613f  d009    bne FRMEND                 ; BRANCH - RTP
.label L6141:
6141  20686c  jsr ACCEL                  ; ACCELERATE (MOVE) MODULE
6144  204f6d  jsr DECODE                 ; DISTANCE DECODE
6147  201c71  jsr SCAPCHG                ; LUNARSCAPE CHANGE
.label FRMEND:
614a  a522    lda GAMODE                 ;
614c  f05b    beq ATRCHK                 ; ATTRACT
614e  20ab62  jsr TYPE                   ; SET GAME TYPE [NOT IN ATTRACT]
6151  2422    bit GAMODE                 ;
6153  3033    bmi MOTCHK                 ; MOTCHK
6155  7055    bvs PLYCHK                 ;
6157  a200    ldx #$00                   ; FLASH START/SELECT LEDS
6159  a586    lda FRAME                  ;
615b  2910    and #$10                   ; ON/OFF 16 FRAMES
615d  d002    bne L6161                  ;
615f  a210    ldx #$10                   ; NOT (BIT 4) SETS LEDS
.label L6161:
6161  a90f    lda #$0f                   ;
6163  205f79  jsr io_lamps_set           ; SET LEDS & ZP STATUS BYTE
6166  2c0024  bit IO_in1_start           ; CHECK START SWITCH
6169  3006    bmi L6171                  ; BRANCH - START SWITCH PUSHES
616b  a940    lda #$40                   ; ELSE - INITIALIZE DEBOUNCE COUNT
616d  8525    sta STRTCNT                ;
616f  d004    bne L6175                  ; ALWAYS
.label L6171:
6171  0625    asl STRTCNT                ; 2 SHIFTS (2 FRAMES) = DEBOUNCE
6173  b00d    bcs L6182                  ; DEBOUNCED
.label L6175:
6175  245d    bit COLFLG                 ; COLLISION?
6177  100c    bpl RTMAIN                 ; BRANCH-NO
6179  201362  jsr ResetGameState         ; RESET MISSION
617c  a910    lda #$10                   ; FREE PLAY
617e  8522    sta GAMODE                 ;
6180  d003    bne RTMAIN                 ;
.label L6182:
6182  4c4060  jmp PLYSTRT                ; INITIALIZE PLAYER ALPH. DATA & MAJOR
.label RTMAIN:
6185  4c6260  jmp MAINLP                 ; RETURN TO MAIN LOOP
.label MOTCHK:
6188  2462    bit M_CLFL                 ; CHECK FOR HARD LANDING
618a  500e    bvc L619a                  ; NOT HARD (BRANCH)
618c  245c    bit Z5c                    ; WAIT FOR MODULE FALL (- VELY)
618e  1004    bpl L6194                  ;
6190  245d    bit COLFLG                 ; THEN - CHECK FOR IMPACT
6192  3006    bmi L619a                  ; IMPACT - BRANCH
.label L6194:
6194  20686c  jsr ACCEL                  ; ELSE - ACCELERATE MODULE (MOVE)
6197  204f6d  jsr DECODE                 ; AND DECODE MODULE TO SCAPE DISTANCE
.label L619a:
619a  a586    lda FRAME                  ; MOTION [LAND/CRASH]
619c  4a      lsr                        ;
619d  b0e6    bcs RTMAIN                 ;
619f  e656    inc INDEX                  ; STEP THROUGH LAND/CRASH SEQUENCE
61a1  10e2    bpl RTMAIN                 ;
61a3  0656    asl INDEX                  ; INDEX=0
61a5  a562    lda M_CLFL                 ; SET TO INITIALIZE ATTRACT
61a7  855d    sta COLFLG                 ;
.label ATRCHK:
61a9  4c0860  jmp dogame                 ; GO TO ATTRACT (PENDING CREDIT)
.label PLYCHK:
61ac  a55d    lda COLFLG                 ; PLAY
61ae  3028    bmi game_next_level_setup  ;
61b0  20aa64  jsr ABORT                  ;
61b3  2497    bit CRDTFLG                ;
61b5  300c    bmi abort_button_handler   ; CONTINUE (PLAYER HAS CREDIT)
61b7  a58d    lda TIMER                  ;
61b9  c905    cmp #$05                   ; ATTRACT MODE AFTER 5 SECONDS
61bb  9003    bcc L61c0                  ;
61bd  4c0160  jmp start                  ; GO TO ATTRACT
.label L61c0:
61c0  4c6260  jmp MAINLP                 ; RETURN TO MAIN LOOP
.label abort_button_handler:
61c3  2c0524  bit IO_in1_abort           ; RESET ONLY W/CREDIT
61c6  3006    bmi L61ce                  ;
61c8  a940    lda #$40                   ;
61ca  8568    sta RSTDEB                 ; INITIALIZE DEBOUNCE
61cc  d0f2    bne L61c0                  ; ALWAYS, RETURN TO MAINLP (NO RESET)
.label L61ce:
61ce  0668    asl RSTDEB                 ;
61d0  90ee    bcc L61c0                  ; DEBOUNCE RESET (2 SHIFTS = 48. MS)
61d2  a964    lda #$64                   ; 0x64 = ABTCNT
61d4  8556    sta INDEX                  ;
61d6  d0e8    bne L61c0                  ; ALWAYS, RETURN TO MAINLP
.label game_next_level_setup:
61d8  20e06b  jsr LNDADR                 ; DO SCORING
61db  a55d    lda COLFLG                 ;
61dd  8562    sta M_CLFL                 ; SET MOTION FLAG
61df  0a      asl                        ;
61e0  d007    bne L61e9                  ;
61e2  a000    ldy #$00                   ; GIVE BONUS FUEL ON GOOD LANDINGS
61e4  a950    lda #$50                   ; BNFUEL = 0050
61e6  201363  jsr GIVCRD                 ;
.label L61e9:
61e9  20906b  jsr fuel_lost_to_crash_wrapper ; SUBTRACT LOST FUEL
61ec  209476  jsr DELTA                  ; EXPLOSION DELTAS
61ef  a200    ldx #$00                   ;
61f1  86af    stx ALTITD[0]              ; ALTITUDE=0
61f3  86b0    stx ALTITD[1]              ;
61f5  86b1    stx ALTITD[2]              ;
61f7  a00a    ldy #$0a                   ;
.label L61f9:
61f9  9657    stx INDEX_high,Y           ; CLEAR SCAPE SCROLL FLAG, VELOCITIES, COLLISION FLAG, THRUST
61fb  88      dey                        ;
61fc  10fb    bpl L61f9                  ;
61fe  a920    lda #$20                   ; JUST SLAM SWITCH SOUND
6200  205379  jsr io_audio_set           ;
6203  0622    asl GAMODE                 ; GO TO LAND/CRASH
6205  a901    lda #$01                   ;
6207  8556    sta INDEX                  ; INDEX SET FOR LAND/CRASH
6209  a90a    lda #$0a                   ; SET VELY IN CASE OF HARD LANDING BOUNCE
620b  8561    sta VELY_high              ;
620d  a941    lda #$41                   ; SET GRAVITY IN CASE OF "    "      "
620f  8563    sta GRAVITY                ;
6211  d0ad    bne L61c0                  ; ALWAYS
```
