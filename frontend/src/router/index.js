import { createRouter, createWebHistory } from 'vue-router';

const StreamPage = () => import('../pages/StreamPage.vue');
const CrawlLogsPage = () => import('../pages/CrawlLogsPage.vue');
const AutoSchedulerPage = () => import('../pages/AutoSchedulerPage.vue');

const routes = [
  { path: '/stream', name: 'stream', component: StreamPage },
  { path: '/crawl-logs', name: 'crawl-logs', component: CrawlLogsPage },
  { path: '/auto-scheduler', name: 'auto-scheduler', component: AutoSchedulerPage },
  { path: '/', redirect: '/stream' },
  // WatchlistManagerPage intentionally has no route — it only opens as a
  // Dialog/Sheet from the Stream page's watchlist card (see StreamPage.vue).
  { path: '/:pathMatch(.*)*', redirect: '/stream' },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 };
  },
});

export default router;
