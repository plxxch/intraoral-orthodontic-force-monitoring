/*
 * MONZAX-dsgba.c
 *
 * Sensor firmware for the battery-free, wireless intraoral orthodontic force
 * monitoring system (BWS): MSP430FR2433 + INA333 + Monza X-8k RFID chip.
 * The MCU reads the amplified strain-gauge signal with its 10-bit ADC and
 * writes the result to the RFID chip memory over I2C.
 *
 * Copyright (c) 2024 Pengyu Li
 * SPDX-License-Identifier: MIT
 */

#include<MSP430FR2433.h>
unsigned char RXData[20]= {0};        // Pointer to TX data

unsigned char TXByteCtr;
unsigned char RXByteCtr;
unsigned char Read=0;


unsigned char TXData[10];


unsigned char rx_index=0;
unsigned char tx_index=0;
//unsigned char baseaddr=24;
//unsigned char baseaddr=21;

unsigned char resetflag=50;
unsigned char data=1;
unsigned char n=0x0;

unsigned int ADC_Result=0;

unsigned char Strain[2]={0,0};

void timer(unsigned int t);
void timer_stop(void);

int main(void)
{



while(1)
{
        P1OUT |=BIT1;
       // P2OUT &= ~BIT3;

                          P2OUT |=BIT7;   //AMPLIFIER
                          timer(100);

                          PMMCTL2 |= INTREFEN;

                                                             //150
                                               P2OUT |=BIT6;    //bridge supply
                                                                                    // Enable internal reference
                                                           timer(100);           //The adc pin need times to be charged

                                               ADCCTL0 |= ADCENC | ADCSC;                           // Sampling and conversion start
                                               __bis_SR_register(LPM3_bits | GIE);                  // LPM0, ADC_ISR will force exit

                                               //timer(1000);
                                               P2OUT &= ~BIT6;
                                               PMMCTL2 &= INTREFEN;
                                              // timer(150); //1000   chip start time 2ms

//if(data==1)
//{

                              TXData[0]=0;
                              TXData[1]=24;  //21 nvm 24
                              TXData[2]=Strain[0];
                              TXData[3]=Strain[1];

//                              if(resetflag==2)
//                              {
//                              TXData[1]=21;  //21 nvm 24
//                              TXData[2]=0x0;
//                              TXData[3]=0x4;//0x04; current is 0x0
//                              }

                              if(resetflag==0)
                              {
                                  TXData[1]=21;
                                  TXData[2]=0x0;
                                  TXData[3]=0x0;//0x04; current is 0x0
                                 // resetflag=10;
                              }

                             // data=0;

//}
//        else
//        {
//                              TXData[0]=0;
//                              TXData[1]=26;
//
//
//
//                             TXData[2]=n;
//                             n=~n;
//                                TXData[3]=n;//0x04;
//                                data=1;
//
//        }

                                                Read=0;
                                                TXByteCtr =4;
                                                tx_index=0;
//
                                                UCB0I2CSA = 0x6E;   //0x68, 0x6A, 0x6C, 0x6E
                                                UCB0IFG &= ~(UCTXIFG + UCRXIFG);       // Clear any pending interrupts
                                                UCB0IE &= ~UCRXIE;                       // Disable RX interrupt
                                                UCB0IE |= UCTXIE;                        // Enable TX interrupt


                                                UCB0CTLW0 |= UCTR + UCTXSTT;             // I2C TX, start condition

                                             __bis_SR_register(LPM3_bits + GIE);



//P3OUT |=BIT0;
             timer(200); // 1000 //memory write time 5ms for 32 bit

         //    P3OUT &= ~BIT0;
                                             P1OUT &= ~BIT1;



         timer(15000);
         //timer(30000);
         __no_operation();
       //  __bis_SR_register(LPM3_bits + GIE);
         if(resetflag>0)
         {
         resetflag--;
         }
}


}





#if defined(__TI_COMPILER_VERSION__) || defined(__IAR_SYSTEMS_ICC__)
#pragma vector = USCI_B0_VECTOR
__interrupt void USCIB0_ISR(void)
#elif defined(__GNUC__)
void __attribute__ ((interrupt(USCI_B0_VECTOR))) USCIB0_ISR (void)
#else
#error Compiler not supported!
#endif
{
  switch(__even_in_range(UCB0IV,USCI_I2C_UCBIT9IFG))
  {
        case USCI_NONE: break;                        // Vector 0: No interrupts break;
        case USCI_I2C_UCALIFG: break;
        case USCI_I2C_UCNACKIFG:
            UCB0CTL1 |= UCTXSTT;                      //resend start if NACK

          break;                                      // Vector 4: NACKIFG break;
        case USCI_I2C_UCSTTIFG: break;                // Vector 6: STTIFG break;
        case USCI_I2C_UCSTPIFG: break;                // Vector 8: STPIFG break;
        case USCI_I2C_UCRXIFG3: break;                // Vector 10: RXIFG3 break;
        case USCI_I2C_UCTXIFG3: break;                // Vector 14: TXIFG3 break;
        case USCI_I2C_UCRXIFG2: break;                // Vector 16: RXIFG2 break;
        case USCI_I2C_UCTXIFG2: break;                // Vector 18: TXIFG2 break;
        case USCI_I2C_UCRXIFG1: break;                // Vector 20: RXIFG1 break;
        case USCI_I2C_UCTXIFG1: break;                // Vector 22: TXIFG1 break;
        case USCI_I2C_UCRXIFG0:                 // Vector 24: RXIFG0 break;


            

            if (RXByteCtr)
            {
                RXByteCtr--;
                RXData[rx_index] = UCB0RXBUF;
                rx_index++;
            }

            if (RXByteCtr == 1)
            {
              UCB0CTLW0 |= UCTXSTP;
            }
            else if (RXByteCtr == 0)
            {
              UCB0IE &= ~UCRXIE;

              __bic_SR_register_on_exit(LPM3_bits);      // Exit LPM0
            }



            break;
        case USCI_I2C_UCTXIFG0:

            switch(Read)
                                  {
                                    case 1:         //Read

                                if (TXByteCtr)                                // Check TX byte counter
                                   {

                                    TXByteCtr--;

                                    UCB0TXBUF =TXData[TXByteCtr] ;            // Load TX buffer
                                                                 // Decrement TX byte counter
                                   }
                                else
                                   {

                                    rx_index=0;
                                    UCB0IE |= UCRXIE;              // Enable RX interrupt
                                    UCB0IE &= ~UCTXIE;             // Disable TX interrupt
                                    UCB0CTLW0 &= ~UCTR;            // Switch to receiver

                                    UCB0CTLW0 |= UCTXSTT;          // Send repeated start
                                    if (RXByteCtr == 1)
                                    {
                                                      //Must send stop since this is the N-1 byte
                                     while((UCB0CTLW0 & UCTXSTT));
                                     UCB0CTLW0 |= UCTXSTP;      // Send stop condition
                                                  }
                                   }
                                break;

                                    case 0:         //write
                                        if (TXByteCtr)                                // Check TX byte counter
                                                 {
                                                   TXByteCtr--;

                                                  UCB0TXBUF = TXData[tx_index];
                                                  tx_index++;
                                                 }
                                              else
                                                 {

                                                   UCB0CTLW0 |= UCTXSTP;      // Send stop condition
                                                   UCB0IE &= ~UCTXIE;                       // disable TX interrupt
                                                 //  timer(100);

                                                   __bic_SR_register_on_exit(LPM3_bits);      // Exit LPM0

//
                                  }
                                    default:
                                                 __no_operation();
                                                 break;
                                  }

          break;                                      // Vector 26: TXIFG0 break;
        case USCI_I2C_UCBCNTIFG: break;               // Vector 28: BCNTIFG
        case USCI_I2C_UCCLTOIFG: break;               // Vector 30: clock low timeout
        case USCI_I2C_UCBIT9IFG: break;               // Vector 32: 9th bit
        default: break;
  }
}

#pragma vector=ADC_VECTOR
__interrupt void ADC_ISR(void)
{
    switch(__even_in_range(ADCIV,ADCIV_ADCIFG))
    {
        case ADCIV_NONE:
            break;
        case ADCIV_ADCOVIFG:
            break;
        case ADCIV_ADCTOVIFG:
            break;
        case ADCIV_ADCHIIFG:
            break;
        case ADCIV_ADCLOIFG:
            break;
        case ADCIV_ADCINIFG:
            break;
        case ADCIV_ADCIFG:
            ADC_Result = ADCMEM0;

            Strain[0] = (unsigned char) (ADC_Result >> 8) & 0xFF;  //1011111101 奔︗
            Strain[1] = (unsigned char) ADC_Result & 0xFF;  //︗

            __bic_SR_register_on_exit(LPM3_bits);            // Clear CPUOFF bit from LPM0
            break;
        default:
            break;
    }
}







#pragma vector = TIMER0_A0_VECTOR
__interrupt void Timer_A (void)

{
    TA0CTL=MC_0;
   __bic_SR_register_on_exit(LPM3_bits);

}


void timer(unsigned int t)    //For delay
{
    TA0CTL=MC_0;

    TA0CCTL0=CCIE;
    TA0CCR0=t;
    TA0CTL=TASSEL_1 +MC_1 + TACLR;
    __bis_SR_register(LPM3_bits + GIE);
}

void timer_stop()
{
    TA0CTL=MC_0;
}

