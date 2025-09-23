import { BskyAgent } from '@atproto/api'

const agent = new BskyAgent({
  service: 'https://bsky.social'
})

await agent.login({
  identifier: 'kxena408.bsky.social',
  password: 'LIGHTHOUSE'
})