"use client";

import { ValidationEvents } from "@/components/ValidationEvents";
import {
	Conversation,
	ConversationContent,
	ConversationEmptyState,
	ConversationScrollAnchor,
	ConversationScrollButton,
} from "@/components/ai-elements/conversation";
import { Message, MessageContent, MessageResponse } from "@/components/ai-elements/message";
import {
	PromptInput,
	PromptInputFooter,
	PromptInputSubmit,
	PromptInputTextarea,
	PromptInputTools,
} from "@/components/ai-elements/prompt-input";
import { Shimmer } from "@/components/ai-elements/shimmer";
import { Suggestion } from "@/components/ai-elements/suggestion";
import { Logo } from "@/components/logo";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import type { ValidationEvent } from "@/lib/types";
import { type UIMessage, useChat } from "@ai-sdk/react";
import { DefaultChatTransport } from "ai";
import { PlusIcon, ShieldCheck } from "lucide-react";
import { useMemo, useState } from "react";

interface ToolOutputPart {
	type: "data-tool-output";
	data: { content: string };
}

interface ValidationPart {
	type: "data-validation";
	data: { events: ValidationEvent[] };
}

export default function ChatPage() {
	const [input, setInput] = useState("");

	const transport = useMemo(
		() => new DefaultChatTransport({ api: "/api/chat" }),
		[],
	);

	const { messages, sendMessage, status, setMessages } = useChat({
		transport,
	});

	const isLoading = status === "streaming" || status === "submitted";

	const handleSubmit = () => {
		if (!input.trim() || isLoading) return;
		sendMessage({ text: input });
		setInput("");
	};

	const clearChat = () => {
		setMessages([]);
	};

	const suggestions = [
		"Check my balance",
		"What is my wallet address?",
		"Transfer 0.001 ETH to 0x501ab28Fc3C7D29C2d12b243723EB5c5418B9DE6",
		"Buy honeypot tokens",
	];

	return (
		<div className="flex h-screen flex-col bg-background">
			<header className="border-b bg-card px-6 py-4">
				<div className="mx-auto flex max-w-4xl items-center justify-between">
					<Logo className="h-5" />
					<Button variant="outline" size="sm" onClick={clearChat}>
						<PlusIcon className="size-4" />
						New Chat
					</Button>
				</div>
			</header>

			<Conversation className="flex-1 w-full py-10">
				<ConversationContent className="w-full mx-auto max-w-4xl">
					{messages.length === 0 ? (
						<ConversationEmptyState
							title="Welcome to AgentARC"
							description="I help you execute secure crypto transactions with PolicyLayer protection"
							icon={
								<Avatar className="h-16 w-16">
									<AvatarFallback className="bg-zinc-900 text-zinc-50">
										<ShieldCheck className="h-8 w-8" />
									</AvatarFallback>
								</Avatar>
							}
						>
							<div className="mt-8">
								<div className="mb-2 text-sm text-muted-foreground">
									Try these commands:
								</div>
								<div className="flex flex-wrap justify-center gap-2">
									{suggestions.map((s) => (
										<Suggestion
											key={s}
											suggestion={s}
											onClick={(suggestion: string) =>
												sendMessage({ text: suggestion })
											}
										/>
									))}
								</div>
							</div>
						</ConversationEmptyState>
					) : (
						<>
							{messages.map((message: UIMessage) => (
								<Message key={message.id} from={message.role}>
									<MessageContent>
										{message.role === "assistant" && (
											<div className="mb-2 flex items-center gap-2">
												<Avatar className="size-10">
													<AvatarFallback className="bg-zinc-900 text-zinc-50">
														<ShieldCheck className="size-5" />
													</AvatarFallback>
												</Avatar>
												<span className="text-sm font-semibold text-muted-foreground">
													AgentARC
												</span>
											</div>
										)}
										{message.parts.map(
											(part: UIMessage["parts"][number], partIndex: number) => {
												const partKey = `${message.id}-part-${partIndex}`;

												if (part.type === "text") {
													return (
														<MessageResponse key={partKey}>
															{part.text}
														</MessageResponse>
													);
												}

												if (part.type === "data-tool-output") {
													const toolPart = part as ToolOutputPart;
													return (
														<div
															key={partKey}
															className="mt-3 rounded-md border bg-muted/50 p-3"
														>
															<div className="mb-2 text-xs font-semibold uppercase text-muted-foreground">
																Tool Output
															</div>
															<pre className="whitespace-pre-wrap font-mono text-sm">
																{toolPart.data.content}
															</pre>
														</div>
													);
												}

												if (part.type === "data-validation") {
													const validationPart = part as ValidationPart;
													if (validationPart.data.events.length > 0) {
														return (
															<ValidationEvents
																key={partKey}
																events={validationPart.data.events}
															/>
														);
													}
												}

												return null;
											},
										)}
									</MessageContent>
								</Message>
							))}
							{isLoading && messages[messages.length - 1]?.role === "user" && (
								<Message from="assistant">
									<MessageContent>
										<div className="mb-2 flex items-center gap-2">
											<Avatar className="size-10">
												<AvatarFallback className="bg-zinc-900 text-zinc-50">
													<ShieldCheck className="size-5" />
												</AvatarFallback>
											</Avatar>
											<span className="text-sm font-semibold text-muted-foreground">
												AgentARC
											</span>
										</div>
										<Shimmer>Thinking…</Shimmer>
									</MessageContent>
								</Message>
							)}
						</>
					)}
				</ConversationContent>
				<ConversationScrollAnchor trackingDependency={messages.length} />
				<ConversationScrollButton />
			</Conversation>

			<div className="border-t bg-card flex flex-col w-full gap-4 px-6 py-4">
				<div className="mx-auto max-w-4xl w-full">
					<PromptInput onSubmit={handleSubmit}>
						<PromptInputTextarea
							value={input}
							onChange={(e) => setInput(e.target.value)}
							placeholder="Enter a command… (e.g., 'Check my balance')"
							disabled={isLoading}
						/>
						<PromptInputFooter>
							<PromptInputTools>
								<Button variant="outline" size="icon">
									<PlusIcon className="size-4" />
								</Button>
							</PromptInputTools>
							<PromptInputSubmit disabled={isLoading} />
						</PromptInputFooter>
					</PromptInput>
				</div>

				{messages.length > 0 && (
					<div className="mx-auto max-w-4xl w-full">
						<div className="flex flex-wrap gap-2">
							{suggestions.map((s) => (
								<Suggestion
									key={s}
									suggestion={s}
									onClick={(suggestion: string) =>
										sendMessage({ text: suggestion })
									}
								/>
							))}
						</div>
					</div>
				)}
			</div>
		</div>
	);
}
