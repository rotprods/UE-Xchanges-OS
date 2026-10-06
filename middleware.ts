import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

// Routes that require authentication
const PROTECTED_API_ROUTES = ["/api/trade", "/api/settings"];
const PROTECTED_PAGES = ["/settings"];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Check if this is a protected API route
  const isProtectedAPI = PROTECTED_API_ROUTES.some((route) =>
    pathname.startsWith(route)
  );

  // Check if this is a protected page
  const isProtectedPage = PROTECTED_PAGES.some((route) =>
    pathname.startsWith(route)
  );

  if (!isProtectedAPI && !isProtectedPage) {
    return NextResponse.next();
  }

  // Check for auth cookie
  const authToken = request.cookies.get("chronos_auth")?.value;
  const adminPassword = process.env.ADMIN_PASSWORD;

  // If no admin password is set, allow everything (dev mode)
  if (!adminPassword) {
    return NextResponse.next();
  }

  // Validate the auth token
  if (authToken === adminPassword) {
    return NextResponse.next();
  }

  // For API routes, return 401
  if (isProtectedAPI) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  // For pages, redirect to login
  const loginUrl = new URL("/login", request.url);
  loginUrl.searchParams.set("from", pathname);
  return NextResponse.redirect(loginUrl);
}

export const config = {
  matcher: ["/settings/:path*", "/api/trade/:path*", "/api/settings/:path*"],
};
