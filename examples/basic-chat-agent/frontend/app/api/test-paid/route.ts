/**
 * Test Paid API Endpoint
 * This is a mock endpoint for testing x402 payments
 * Returns a fake transaction hash for demonstration
 */

import { NextRequest, NextResponse } from 'next/server';

export async function POST(req: NextRequest) {
  const xPayment = req.headers.get('X-PAYMENT');

  // Step 1: No payment - return 402
  if (!xPayment) {
    return NextResponse.json({
      x402Version: 1,
      message: 'Payment required',
      methods: [{
        scheme: 'exact',
        network: process.env.X402_NETWORK || 'base-sepolia',
        maximumAmount: '100000', // $0.10 USDC
        asset: process.env.USDC_ADDRESS || '0x036CbD53842c5426634e7929541eC2318f3dCF7e',
        recipient: process.env.YOUR_WALLET_ADDRESS || '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb',
        resource: '/api/test-paid',
        description: 'Test sentiment analysis (demo)',
        timeout: 300000
      }]
    }, { status: 402 });
  }

  // Step 2: Decode and verify payment
  let paymentPayload;
  try {
    paymentPayload = JSON.parse(
      Buffer.from(xPayment, 'base64').toString('utf-8')
    );
  } catch (error) {
    return NextResponse.json({
      error: 'Invalid payment payload'
    }, { status: 402 });
  }

  console.log('💰 Payment received from:', paymentPayload.payload.authorization.from);
  console.log('💵 Amount:', parseInt(paymentPayload.payload.authorization.value) / 1_000_000, 'USDC');

  // Step 3: Verify payment with facilitator
  const FACILITATOR_URL = process.env.X402_FACILITATOR_URL || 'https://x402.org/facilitator';

  try {
    const verifyResponse = await fetch(`${FACILITATOR_URL}/verify`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        paymentPayload,
        paymentRequirements: {
          scheme: 'exact',
          network: paymentPayload.network,
          maxAmountRequired: '100000',
          asset: process.env.USDC_ADDRESS || '0x036CbD53842c5426634e7929541eC2318f3dCF7e',
          payTo: process.env.YOUR_WALLET_ADDRESS || '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb',
          resource: `${req.nextUrl.origin}/api/test-paid`,
          description: 'Test sentiment analysis (demo)',
          mimeType: 'application/json',
          maxTimeoutSeconds: 300
        }
      })
    });

    const verification = await verifyResponse.json();

    console.log('🔍 Facilitator response:', JSON.stringify(verification, null, 2));

    if (!verification.isValid) {
      console.error('❌ Payment verification failed:', verification.invalidReason || verification);
      return NextResponse.json({
        error: 'Payment verification failed',
        details: JSON.stringify(verification.invalidReason || verification)
      }, { status: 402 });
    }

    console.log('✅ Payment verified');

  } catch (error: any) {
    console.error('❌ Error verifying payment:', error);
    return NextResponse.json({
      error: 'Failed to verify payment',
      message: error.message
    }, { status: 500 });
  }

  // Step 4: Settle payment on-chain (get real transaction hash)
  let settlementResult;
  try {
    console.log('🔄 Settling payment on-chain...');

    const settleResponse = await fetch(`${FACILITATOR_URL}/settle`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        paymentPayload,
        paymentRequirements: {
          scheme: 'exact',
          network: paymentPayload.network,
          maxAmountRequired: '100000',
          asset: process.env.USDC_ADDRESS || '0x036CbD53842c5426634e7929541eC2318f3dCF7e',
          payTo: process.env.YOUR_WALLET_ADDRESS || '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb',
          resource: `${req.nextUrl.origin}/api/test-paid`,
          description: 'Test sentiment analysis (demo)',
          mimeType: 'application/json',
          maxTimeoutSeconds: 300
        }
      })
    });

    const settlementText = await settleResponse.text();
    console.log('🔍 Settlement response status:', settleResponse.status);
    console.log('🔍 Settlement response body:', settlementText);

    // Try to parse settlement response
    if (settlementText && settlementText.trim()) {
      try {
        settlementResult = JSON.parse(settlementText);
        console.log('🔍 Settlement parsed:', JSON.stringify(settlementResult, null, 2));
      } catch (e) {
        console.error('❌ Failed to parse settlement response:', e);
        settlementResult = null;
      }
    } else {
      console.warn('⚠️ Empty settlement response');
      settlementResult = null;
    }

    // Check if settlement succeeded
    const settlementSucceeded = settlementResult && (
      settlementResult.success === true ||
      settlementResult.transactionHash ||
      settlementResult.txHash ||
      settlementResult.hash
    );

    if (!settlementSucceeded && settleResponse.status >= 400) {
      console.error('❌ Settlement failed:', settlementResult?.error || 'Unknown error');
      return NextResponse.json({
        error: 'Payment settlement failed',
        details: settlementResult?.error || `Status: ${settleResponse.status}`
      }, { status: 500 });
    }

    if (settlementSucceeded) {
      console.log('✅ Payment settled on-chain');
      console.log('📝 Transaction hash:', settlementResult.transactionHash || settlementResult.txHash || settlementResult.hash);
    } else {
      console.warn('⚠️ Settlement status unclear - continuing anyway (verification passed)');
    }

  } catch (error: any) {
    console.error('❌ Error settling payment:', error);
    return NextResponse.json({
      error: 'Failed to settle payment',
      message: error.message
    }, { status: 500 });
  }

  // Step 5: Process the sentiment analysis
  try {
    // Get request body
    const body = await req.json();
    const { text } = body;

    // Simple sentiment analysis (demo)
    const positiveWords = ['love', 'great', 'awesome', 'excellent', 'amazing', 'wonderful', 'fantastic'];
    const negativeWords = ['hate', 'terrible', 'awful', 'bad', 'horrible', 'worst', 'disappointing'];

    const lowerText = (text || '').toLowerCase();
    const positiveCount = positiveWords.filter(word => lowerText.includes(word)).length;
    const negativeCount = negativeWords.filter(word => lowerText.includes(word)).length;

    let sentiment = 'neutral';
    let confidence = 50;

    if (positiveCount > negativeCount) {
      sentiment = 'positive';
      confidence = Math.min(95, 60 + positiveCount * 10);
    } else if (negativeCount > positiveCount) {
      sentiment = 'negative';
      confidence = Math.min(95, 60 + negativeCount * 10);
    }

    // Extract transaction hash from settlement result
    const txHash = settlementResult ? (
      settlementResult.transactionHash ||
      settlementResult.txHash ||
      settlementResult.hash ||
      null
    ) : null;

    // Return with transaction info from blockchain settlement
    return NextResponse.json({
      sentiment,
      confidence,
      positiveWords: positiveCount,
      negativeWords: negativeCount,
      text,
      // Transaction info from on-chain settlement
      transactionHash: txHash,
      network: settlementResult?.network || paymentPayload.network,
      blockNumber: settlementResult?.blockNumber,
      payer: paymentPayload.payload.authorization.from,
      amount: paymentPayload.payload.authorization.value,
      timestamp: new Date().toISOString()
    });

  } catch (error: any) {
    console.error('Payment processing error:', error);
    return NextResponse.json({
      error: 'Payment verification failed',
      message: error.message
    }, { status: 402 });
  }
}
