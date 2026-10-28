/*****************************************************************************/
/* _SYSTEM_PRE_INIT.C          - Perform any application-specific inits      */
/*                                                                           */
/* Copyright (c) 2015 Texas Instruments Incorporated                         */
/* http://www.ti.com/                                                        */
/*                                                                           */
/*  Redistribution and  use in source  and binary forms, with  or without    */
/*  modification,  are permitted provided  that the  following conditions    */
/*  are met:                                                                 */
/*                                                                           */
/*     Redistributions  of source  code must  retain the  above copyright    */
/*     notice, this list of conditions and the following disclaimer.         */
/*                                                                           */
/*     Redistributions in binary form  must reproduce the above copyright    */
/*     notice, this  list of conditions  and the following  disclaimer in    */
/*     the  documentation  and/or   other  materials  provided  with  the    */
/*     distribution.                                                         */
/*                                                                           */
/*     Neither the  name of Texas Instruments Incorporated  nor the names    */
/*     of its  contributors may  be used to  endorse or  promote products    */
/*     derived  from   this  software  without   specific  prior  written    */
/*     permission.                                                           */
/*                                                                           */
/*  THIS SOFTWARE  IS PROVIDED BY THE COPYRIGHT  HOLDERS AND CONTRIBUTORS    */
/*  "AS IS"  AND ANY  EXPRESS OR IMPLIED  WARRANTIES, INCLUDING,  BUT NOT    */
/*  LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR    */
/*  A PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT    */
/*  OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,    */
/*  SPECIAL,  EXEMPLARY,  OR CONSEQUENTIAL  DAMAGES  (INCLUDING, BUT  NOT    */
/*  LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,    */
/*  DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY    */
/*  THEORY OF  LIABILITY, WHETHER IN CONTRACT, STRICT  LIABILITY, OR TORT    */
/*  (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE    */
/*  OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.     */
/*                                                                           */
/*****************************************************************************/

/*****************************************************************************/
/* _SYSTEM_PRE_INIT() - _system_pre_init() is called in the C/C++ startup    */
/* routine (_c_int00()) and provides a mechanism for the user to             */
/* insert application specific low level initialization instructions prior   */
/* to calling main().  The return value of _system_pre_init() is used to     */
/* determine whether or not C/C++ global data initialization will be         */
/* performed (return value of 0 to bypass C/C++ auto-initialization).        */
/*                                                                           */
/* PLEASE NOTE THAT BYPASSING THE C/C++ AUTO-INITIALIZATION ROUTINE MAY      */
/* RESULT IN PROGRAM FAILURE.                                                */
/*                                                                           */
/* The version of _system_pre_init() below is skeletal and is provided to    */
/* illustrate the interface and provide default behavior.  To replace this   */
/* version rewrite the routine and include it as part of the current project.*/
/* The linker will include the updated version if it is linked in prior to   */
/* linking with the C/C++ runtime library.                                   */
/*****************************************************************************/
#include<MSP430FR2433.h>
extern "C" int _system_pre_init(void)
{
    WDTCTL = WDTPW | WDTHOLD;                         // Stop watchdog timer
      P1DIR=0XFF;
      P1OUT=0X0;
      P2DIR=0XFF;
      P2OUT=0X0;
      P3DIR=0XFF;
      P3OUT=0X0;


      FRCTL0 = FRCTLPW | NWAITS_1;

              __bis_SR_register(SCG0);                           // disable FLL
              CSCTL3 |= SELREF__REFOCLK;                         // Set REFO as FLL reference source
              CSCTL0 = 0;                                        // clear DCO and MOD registers
              CSCTL1 &= ~(DCORSEL_7);                            // Clear DCO frequency select bits first
              CSCTL1 |= DCORSEL_5;                               // Set DCO = 16MHz
              CSCTL2 = FLLD_0 + 487;                             // DCOCLKDIV = 16MHz
              __delay_cycles(3);
              __bic_SR_register(SCG0);                           // enable FLL
            //  while(CSCTL7 & (FLLUNLOCK0 | FLLUNLOCK1));         // FLL locked



            CSCTL4 = SELMS__DCOCLKDIV; // set default REFO(~32768Hz) as ACLK source, ACLK = 32768Hz










           // P1OUT |=BIT1;  //MONZA




       P1SEL0 |= BIT2 | BIT3;                            // I2C pins

        // Disable the GPIO power-on default high-impedance mode
        // to activate previously configured port settings
        PM5CTL0 &= ~LOCKLPM5;

       // P1IFG &= ~BIT4;

        // Configure USCI_B0 for I2C mode
        UCB0CTLW0 |= UCSWRST;                             // put eUSCI_B in reset state
        UCB0CTLW0 |= UCMODE_3 | UCMST | UCSYNC;                    // I2C master mode, SMCLK

        UCB0BRW =128;//8;                                    // baudrate = SMCLK(16MHz) / 128
       // UCB0BRW =8;                                    // baudrate = SMCLK(1 MHz) / 8
        UCB0CTLW0 &=~ UCSWRST;                            // clear reset register
        UCB0IE |= UCNACKIE;                     // transmit and NACK interrupt enable


        //configure the ADC

        SYSCFG2 |= ADCPCTL4;

            // Disable the GPIO power-on default high-impedance mode to activate
            // previously configured port settings
            PM5CTL0 &= ~LOCKLPM5;

            // Configure ADC10
            ADCCTL0 |= ADCSHT_6 | ADCON;                             // ADCON, S&H=16 ADC clks
            ADCCTL1 |= ADCSHP | ADCDIV_7;                                       // ADCCLK = MODOSC; sampling timer
            ADCCTL2 |= ADCRES;                                       // 10-bit conversion results
            ADCMCTL0 |= ADCINCH_4 | ADCSREF_1;                                   //  A1 ADC input select; Vref=AVCC 0, 1.5v:1.
            ADCIE |= ADCIE0;                                         // Enable ADC conv complete interrupt                                    // Enable ADC conv complete interrupt
            PMMCTL0_H = PMMPW_H;                                      // Unlock the PMM registers



    //

    //    TA0CCTL0 = CCIE;                          // CCR0 interrupt enabled
    //     TA0CCR0 =32760;//1688;//3276;
    //     TA0CTL=TASSEL_1 +MC_1 + TACLR;

        __bis_SR_register(GIE);               // Enter LPM0 w/ interrupts

                //__bis_SR_register(GIE);               // Enter LPM0 w/ interrupts
    return 1;
}
