import { NextResponse } from 'next/server'

export function databaseUnavailableResponse(resource: string) {
  return NextResponse.json(
    {
      success: false,
      error: `${resource} requires a configured database`,
    },
    { status: 503 }
  )
}
