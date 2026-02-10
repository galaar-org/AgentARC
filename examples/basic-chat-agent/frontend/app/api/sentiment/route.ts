/**
 * Real Sentiment Analysis API using OpenAI
 * Accepts x402 payments
 */

import { NextRequest, NextResponse } from 'next/server';
import OpenAI from 'openai';

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

export async function POST(req: NextRequest) {
  const xPayment = req.headers.get('X-PAYMENT');

  // Step 1: No payment - return 402
  if (!xPayment) {
    return NextResponse.json({
      x402Version: 1,
      message: 'Payment required for sentiment analysis',
      methods: [{
        scheme: 'exact',
        network: process.env.X402_NETWORK || 'base-sepolia',
        maximumAmount: '100000', // $0.10 USDC
        asset: process.env.USDC_ADDRESS || '0x036CbD53842c5426634e7929541eC2318f3dCF7e',
        recipient: process.env.YOUR_WALLET_ADDRESS || '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb',
        resource: '/api/sentiment',
        description: 'AI-powered sentiment analysis',
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
    const verificationPayload = {
      paymentPayload,
      paymentRequirements: {
        scheme: 'exact',
        network: paymentPayload.network,
        maxAmountRequired: '100000',
        asset: process.env.USDC_ADDRESS || '0x036CbD53842c5426634e7929541eC2318f3dCF7e',
        payTo: process.env.YOUR_WALLET_ADDRESS || '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb',
        resource: `${req.nextUrl.origin}/api/sentiment`,
        description: 'AI-powered sentiment analysis',
        mimeType: 'application/json',
        maxTimeoutSeconds: 300
      }
    };

    console.log('🔍 Sending verification request to:', `${FACILITATOR_URL}/verify`);
    console.log('🔍 Verification payload:', JSON.stringify(verificationPayload, null, 2));

    const verifyResponse = await fetch(`${FACILITATOR_URL}/verify`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(verificationPayload)
    });

    console.log('🔍 Verify response status:', verifyResponse.status);

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
          resource: `${req.nextUrl.origin}/api/sentiment`,
          description: 'AI-powered sentiment analysis',
          mimeType: 'application/json',
          maxTimeoutSeconds: 300
        }
      })
    });

    console.log('🔍 Settlement response status:', settleResponse.status);

    // Get response text first to see what we're dealing with
    const settlementText = await settleResponse.text();
    console.log('🔍 Settlement response body:', settlementText);

    // Try to parse as JSON if not empty
    if (settlementText && settlementText.trim()) {
      try {
        settlementResult = JSON.parse(settlementText);
        console.log('🔍 Settlement parsed:', JSON.stringify(settlementResult, null, 2));
      } catch (e) {
        console.error('❌ Failed to parse settlement response as JSON:', e);
        settlementResult = null;
      }
    } else {
      console.warn('⚠️ Empty settlement response');
      settlementResult = null;
    }

    // Check if settlement succeeded - different facilitators use different formats
    const settlementSucceeded = settlementResult && (
      settlementResult.success === true ||
      settlementResult.transactionHash ||
      settlementResult.txHash ||
      settlementResult.hash
    );

    if (!settlementSucceeded && settleResponse.status >= 400) {
      // Settlement explicitly failed
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
    const { text, language = 'en' } = body;

    if (!text) {
      return NextResponse.json({
        error: 'Missing required field: text'
      }, { status: 400 });
    }

    // Use OpenAI for sentiment analysis
    const completion = await openai.chat.completions.create({
      model: "gpt-3.5-turbo",
      messages: [
        {
          role: "system",
          content: `You are a sentiment analysis expert. Analyze the sentiment of the given text and respond in JSON format with:
{
  "sentiment": "positive" | "negative" | "neutral",
  "confidence": number (0-100),
  "emotions": array of detected emotions,
  "key_phrases": array of important phrases,
  "explanation": brief explanation
}`
        },
        {
          role: "user",
          content: `Analyze the sentiment of this text in ${language}: "${text}"`
        }
      ],
      response_format: { type: "json_object" },
      temperature: 0.3
    });

    const analysis = JSON.parse(completion.choices[0].message.content || '{}');

    // Extract transaction hash from settlement result (different facilitators use different field names)
    const txHash = settlementResult ? (
      settlementResult.transactionHash ||
      settlementResult.txHash ||
      settlementResult.hash ||
      null
    ) : null;

    // Return with transaction info from blockchain settlement
    return NextResponse.json({
      ...analysis,
      text,
      language,
      model: 'gpt-3.5-turbo',
      // Transaction info from on-chain settlement
      transactionHash: txHash,
      network: settlementResult?.network || paymentPayload.network,
      blockNumber: settlementResult?.blockNumber,
      payer: paymentPayload.payload.authorization.from,
      amount: paymentPayload.payload.authorization.value,
      timestamp: new Date().toISOString()
    });

  } catch (error: any) {
    console.error('Error processing sentiment analysis:', error);
    return NextResponse.json({
      error: 'Failed to process sentiment analysis',
      message: error.message
    }, { status: 500 });
  }
}
