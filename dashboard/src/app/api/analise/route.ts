import { NextRequest, NextResponse } from "next/server";
import OpenAI from "openai";

const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

type AnaliseResponse = {
  nome_muda: string;
  instrucoes: string; // separado por ;
  condicoes_ideais: {
    temperatura: string;
    umidade: string;
    luminosidade: string;
    solo: string;
    outros?: string;
  };
};

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const imageBase64 = body.image;

    if (!imageBase64) {
      return NextResponse.json({ error: "Imagem não enviada" }, { status: 400 });
    }

    const imageData = imageBase64.startsWith("data:image")
      ? imageBase64
      : `data:image/jpeg;base64,${imageBase64}`;

    const systemPrompt = `
Você é um especialista em botânica e fala **somente em português**.
Analise a imagem fornecida e retorne **somente JSON válido** no formato:
{
  "nome_muda": "Nome da planta em português",
  "instrucoes": "Instruções de cuidados e manejo em português; separadas por ponto e vírgula;",
  "condicoes_ideais": {
    "temperatura": "temperatura ideal em °C",
    "umidade": "umidade ideal em %",
    "luminosidade": "sol pleno / meia sombra / sombra",
    "solo": "tipo de solo recomendado",
    "outros": "outras condições relevantes se houver"
  }
}
Não adicione texto fora do JSON. Todos os campos devem estar em português.
`;

    const completion = await openai.chat.completions.create({
      model: "gpt-4o",
      messages: [
        { role: "system", content: systemPrompt },
        {
          role: "user",
          content: [
            {
              type: "image_url",
              image_url: { url: imageData }
            }
          ]
        }
      ],
      temperature: 0,
      max_tokens: 1000,
    });

    const message = completion.choices[0]?.message;
    if (!message) {
      return NextResponse.json({ error: "Nenhuma resposta do GPT" }, { status: 500 });
    }

    let rawText = "";
    if (Array.isArray(message.content)) {
      const textPart = message.content.find((c: any) => c.type === "text");
      rawText = textPart?.text || "";
    } else if (typeof message.content === "string") {
      rawText = message.content;
    }

    rawText = rawText.trim().replace(/```json/i, "").replace(/```/i, "").trim();
    rawText = rawText.replace(/\n/g, "").replace(/,\s*}/g, "}").replace(/,\s*]/g, "]");

    let result: AnaliseResponse;
    try {
      result = JSON.parse(rawText);
    } catch {
      return NextResponse.json(
        {
          nome_muda: "Desconhecido",
          instrucoes: rawText,
          condicoes_ideais: {
            temperatura: "-",
            umidade: "-",
            luminosidade: "-",
            solo: "-",
          },
        },
        { status: 200 }
      );
    }

    return NextResponse.json(result);

  } catch (err) {
    console.error(err);
    return NextResponse.json(
      {
        nome_muda: "Erro",
        instrucoes: "Não foi possível analisar a imagem.",
        condicoes_ideais: {
          temperatura: "-",
          umidade: "-",
          luminosidade: "-",
          solo: "-",
        },
      },
      { status: 500 }
    );
  }
}
