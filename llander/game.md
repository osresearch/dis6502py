# Start game

[A34573.1A](https://github.com/historicalsource/lunar-lander/blob/main/A34573.1A) source


```
; Power on and main loop
.func start:
6001  201362  jsr ResetGameState         ; Initialize for attract
6004  a980    lda #$80                   ;
6006  855d    sta COLFLG                 ; Set VOLFLG for initial call to trans to setup lunar major scape

.label dogame:
6008  2497    bit CRDTFLG                ; check for credit
600a  300f    bmi L601b                  ;
600c  a900    lda #$00                   ;
600e  8522    sta GAMODE                 ;
6010  8597    sta CRDTFLG                ;
6012  245d    bit COLFLG                 ;
6014  104c    bpl GameLoop_maybe         ;
6016  201362  jsr ResetGameState         ;
6019  d028    bne L6043                  ;
.label L601b:
601b  a522    lda GAMODE                 ;
601d  d021    bne L6040                  ;
601f  201362  jsr ResetGameState         ;
6022  a9f0    lda #$f0                   ;
6024  a208    ldx #$08                   ;
6026  205f79  jsr io_lamps_set           ;
6029  a200    ldx #$00                   ;
602b  8623    stx PLYMOD                 ;
602d  86a4    stx SCORE                  ;
602f  86a5    stx SCORE_high             ;
6031  a911    lda #$11                   ;
6033  8563    sta GRAVITY                ;
6035  a920    lda #$20                   ;
6037  a698    ldx C_OPT                  ;
6039  d001    bne L603c                  ;
603b  4a      lsr                        ;
.label L603c:
603c  8522    sta GAMODE                 ;
603e  d003    bne L6043                  ;
.label L6040:
6040  203562  jsr game_state_reinit_maybe ;
.label L6043:
6043  20a973  jsr draw_lots_of_stuff     ;
6046  a22c    ldx #$2c                   ;
6048  a0ca    ldy #$ca                   ;
604a  a521    lda LANG                   ;
604c  f004    beq L6052                  ;
604e  a2a0    ldx #$a0                   ;
6050  a0c3    ldy #$c3                   ;
.label L6052:
6052  a522    lda GAMODE                 ;
6054  2920    and #$20                   ;
6056  f004    beq L605c                  ;
6058  a200    ldx #$00                   ;
605a  a0f0    ldy #$f0                   ;
.label L605c:
605c  8e0040  stx IO_vecgen_ram          ;
605f  8c0140  sty D4001                  ;
.label GameLoop_maybe:
6062  a240    ldx #$40                   ;
6064  a004    ldy #$04                   ;
6066  a586    lda FRAME                  ;
6068  4a      lsr                        ;
6069  9004    bcc L606f                  ;
606b  a242    ldx #$42                   ;
606d  a084    ldy #$84                   ;
.label L606f:
606f  8628    stx RAMPTR_high            ;
6071  8427    sty RAMPTR                 ;
6073  a522    lda GAMODE                 ;
6075  2920    and #$20                   ;
6077  d02d    bne L60a6                  ;
6079  209567  jsr draw_even_more_stuff   ;
607c  203965  jsr vec_draw_51ba_table    ;
607f  206765  jsr vec_draw_subroutines   ;
6082  20ad65  jsr draw_ship_prep_maybe   ;
6085  a522    lda GAMODE                 ;
6087  2910    and #$10                   ;
6089  d01b    bne L60a6                  ;
608b  2422    bit GAMODE                 ;
608d  101d    bpl L60ac                  ;
608f  a562    lda M_CLFL                 ;
6091  290f    and #$0f                   ;
6093  f00b    beq L60a0                  ;
6095  a529    lda PTRTMP                 ;
6097  8527    sta RAMPTR                 ;
6099  a52a    lda PTRTMP_high            ;
609b  8528    sta RAMPTR_high            ;
609d  209575  jsr debris_something       ;
.label L60a0:
60a0  20d668  jsr draw_level_over_screen ;
60a3  4cce60  jmp L60ce                  ;
.label L60a6:
60a6  207e68  jsr draw_push_start_screen ;
60a9  4cce60  jmp L60ce                  ;
.label L60ac:
60ac  209d66  jsr debris_update          ;
60af  2422    bit GAMODE                 ;
60b1  5018    bvc L60cb                  ;
60b3  a523    lda PLYMOD                 ;
60b5  d00b    bne L60c2                  ;
60b7  a586    lda FRAME                  ;
60b9  290f    and #$0f                   ;
60bb  c908    cmp #$08                   ;
60bd  d003    bne L60c2                  ;
60bf  200965  jsr ship_vel_decay         ;
.label L60c2:
60c2  209e68  jsr draw_out_of_fuel_screen ;
60c5  20ff67  jsr draw_bonus_maybe       ;
60c8  4cce60  jmp L60ce                  ;
.label L60cb:
60cb  209f79  jsr draw_insert_coin_screen ;
.label L60ce:
60ce  a0de    ldy #$de                   ;
60d0  a94b    lda #$4b                   ;
60d2  a206    ldx #$06                   ;
60d4  20a67e  jsr VecCmd_memcpy          ;
60d7  ad0020  lda IO_in0                 ;
60da  2902    and #$02                   ;
.label L60dc:
60dc  f0fe    beq L60dc                  ;
60de  202d65  jsr dvg_wait_done          ;
60e1  a002    ldy #$02                   ;
60e3  a2f0    ldx #$f0                   ;
60e5  a586    lda FRAME                  ;
60e7  4a      lsr                        ;
60e8  9004    bcc L60ee                  ;
60ea  a2e1    ldx #$e1                   ;
60ec  a042    ldy #$42                   ;
.label L60ee:
60ee  8e0340  stx D4003                  ;
60f1  8c0240  sty D4002                  ;
60f4  8d0030  sta IO_DMAGO               ;
60f7  e686    inc FRAME                  ;
60f9  a200    ldx #$00                   ;
60fb  ad0020  lda IO_in0                 ;
60fe  2904    and #$04                   ;
6100  d002    bne L6104                  ;
6102  a220    ldx #$20                   ;
.label L6104:
6104  a91f    lda #$1f                   ;
6106  205379  jsr io_audio_set           ;
6109  20e662  jsr coin_inserted          ;
610c  201464  jsr thrust_smoothing_maybe ;
610f  2422    bit GAMODE                 ;
6111  3037    bmi L614a                  ;
6113  501f    bvc L6134                  ;
6115  20326b  jsr ship_compute_accel_xy  ;
6118  203c63  jsr ship_command_yaw       ;
611b  20716b  jsr fuel_drain_thrust      ;
611e  201b75  jsr bcd_score_maybe        ;
6121  a501    lda THRUST                 ;
6123  c910    cmp #$10                   ;
6125  d002    bne L6129                  ;
6127  a90f    lda #$0f                   ;
.label L6129:
6129  4a      lsr                        ;
612a  0901    ora #$01                   ;
612c  aa      tax                        ;
612d  a930    lda #$30                   ;
612f  205379  jsr io_audio_set           ;
6132  d00d    bne L6141                  ;
.label L6134:
6134  a920    lda #$20                   ;
6136  a200    ldx #$00                   ;
6138  205379  jsr io_audio_set           ;
613b  a522    lda GAMODE                 ;
613d  2920    and #$20                   ;
613f  d009    bne L614a                  ;
.label L6141:
6141  20686c  jsr ship_update            ;
6144  204f6d  jsr GameRunningLoop        ;
6147  201c71  jsr S711c                  ;
.label L614a:
614a  a522    lda GAMODE                 ;
614c  f05b    beq L61a9                  ;
614e  20ab62  jsr mission_button_handler ;
6151  2422    bit GAMODE                 ;
6153  3033    bmi L6188                  ;
6155  7055    bvs L61ac                  ;
6157  a200    ldx #$00                   ;
6159  a586    lda FRAME                  ;
615b  2910    and #$10                   ;
615d  d002    bne L6161                  ;
615f  a210    ldx #$10                   ;
.label L6161:
6161  a90f    lda #$0f                   ;
6163  205f79  jsr io_lamps_set           ;
6166  2c0024  bit IO_in1_start           ;
6169  3006    bmi L6171                  ;
616b  a940    lda #$40                   ;
616d  8525    sta STRTCNT                ;
616f  d004    bne L6175                  ;
.label L6171:
6171  0625    asl STRTCNT                ;
6173  b00d    bcs L6182                  ;
.label L6175:
6175  245d    bit COLFLG                 ;
6177  100c    bpl L6185                  ;
6179  201362  jsr ResetGameState         ;
617c  a910    lda #$10                   ;
617e  8522    sta GAMODE                 ;
6180  d003    bne L6185                  ;
.label L6182:
6182  4c4060  jmp L6040                  ;
.label L6185:
6185  4c6260  jmp GameLoop_maybe         ;
.label L6188:
6188  2462    bit M_CLFL                 ;
618a  500e    bvc L619a                  ;
618c  245c    bit Z5c                    ;
618e  1004    bpl L6194                  ;
6190  245d    bit COLFLG                 ;
6192  3006    bmi L619a                  ;
.label L6194:
6194  20686c  jsr ship_update            ;
6197  204f6d  jsr GameRunningLoop        ;
.label L619a:
619a  a586    lda FRAME                  ;
619c  4a      lsr                        ;
619d  b0e6    bcs L6185                  ;
619f  e656    inc INDEX                  ;
61a1  10e2    bpl L6185                  ;
61a3  0656    asl INDEX                  ;
61a5  a562    lda M_CLFL                 ;
61a7  855d    sta COLFLG                 ;
.label L61a9:
61a9  4c0860  jmp dogame                 ;
.label L61ac:
61ac  a55d    lda COLFLG                 ;
61ae  3028    bmi game_next_level_setup  ;
61b0  20aa64  jsr abort_procedure_update ;
61b3  2497    bit CRDTFLG                ;
61b5  300c    bmi abort_button_handler   ;
61b7  a58d    lda TIMER                  ;
61b9  c905    cmp #$05                   ;
61bb  9003    bcc call_init_game_thunk   ;
61bd  4c0160  jmp start                  ;
.label call_init_game_thunk:
61c0  4c6260  jmp GameLoop_maybe         ;
.label abort_button_handler:
61c3  2c0524  bit IO_in1_abort           ;
61c6  3006    bmi L61ce                  ;
61c8  a940    lda #$40                   ;
61ca  8568    sta RSTDEB                 ;
61cc  d0f2    bne call_init_game_thunk   ;
.label L61ce:
61ce  0668    asl RSTDEB                 ;
61d0  90ee    bcc call_init_game_thunk   ;
61d2  a964    lda #$64                   ;
61d4  8556    sta INDEX                  ;
61d6  d0e8    bne call_init_game_thunk   ;
.label game_next_level_setup:
61d8  20e06b  jsr score_add_landing_bonus ;
61db  a55d    lda COLFLG                 ;
61dd  8562    sta M_CLFL                 ;
61df  0a      asl                        ;
61e0  d007    bne L61e9                  ;
61e2  a000    ldy #$00                   ;
61e4  a950    lda #$50                   ;
61e6  201363  jsr fuel_increase_limit_9999 ;
.label L61e9:
61e9  20906b  jsr fuel_lost_to_crash_wrapper ;
61ec  209476  jsr landed_choose_random   ;
61ef  a200    ldx #$00                   ;
61f1  86af    stx ALTITD[0]              ;
61f3  86b0    stx ALTITD[1]              ;
61f5  86b1    stx ALTITD[2]              ;
61f7  a00a    ldy #$0a                   ;
.label L61f9:
61f9  9657    stx INDEX_high,Y           ;
61fb  88      dey                        ;
61fc  10fb    bpl L61f9                  ;
61fe  a920    lda #$20                   ;
6200  205379  jsr io_audio_set           ;
6203  0622    asl GAMODE                 ;
6205  a901    lda #$01                   ;
6207  8556    sta INDEX                  ;
6209  a90a    lda #$0a                   ;
620b  8561    sta VELY_high              ;
620d  a941    lda #$41                   ;
620f  8563    sta GRAVITY                ;
6211  d0ad    bne call_init_game_thunk   ;
```
