import NextAuth from "next-auth";
import Google from "next-auth/providers/google";
import Credentials from "next-auth/providers/credentials";

export const { handlers, signIn, signOut, auth } = NextAuth({
  providers: [
    Google({
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
    }),
    Credentials({
      name: "이메일 로그인",
      credentials: {
        email: { label: "이메일", type: "email", placeholder: "team@example.com" },
        password: { label: "비밀번호", type: "password" },
      },
      async authorize(credentials) {
        // Demo mode: accept any email with password "techpulse"
        if (credentials?.password === "techpulse") {
          return {
            id: "1",
            name: (credentials.email as string).split("@")[0],
            email: credentials.email as string,
            role: "member",
          };
        }
        return null;
      },
    }),
  ],
  pages: {
    signIn: "/login",
  },
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.role = (user as any).role || "member";
      }
      return token;
    },
    async session({ session, token }) {
      if (session.user) {
        (session.user as any).role = token.role;
      }
      return session;
    },
  },
});
