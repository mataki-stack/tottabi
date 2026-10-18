(() => {
  "use strict";

  // -------------------------------------------------------------------------
  // State
  // -------------------------------------------------------------------------
  let dataset = null;
  let allVideos = [];
  let videoMap = new Map();
  let countryFlagMap = new Map();

  let userState = {
    favorites: new Set(),
    watched: new Set(),
    watch_later: new Set(),
    notes: {},
  };

  let uiState = {
    currentView: "honeymoon", // 'honeymoon' | 'map' | 'playlists' | 'all'
    layout: "grid", // 'grid' | 'list' | 'timeline'
    searchQuery: "",
    searchDesc: true,
    channel: "all",
    status: "all",
    category: "all",
    season: "all",
    location: "all", // 'all' | 'scope:domestic' | 'scope:overseas' | 'region:...' | 'pref:...' | 'country:...'
    year: "all",
    duration: "all",
    sortBy: "date_desc",
    excludeShorts: false,
    hmIncludeSub: true,
    hmChronological: true,
    mapMode: "japan", // 'japan' | 'world'
    selectedMapLoc: null, // e.g. 'pref:北海道', 'region:東北', 'country:スイス'
    allViewLimit: 60,
    openPlaylists: new Set(),
    modalVideoId: null,
    modalContextList: [],
  };

  // Geographical 12x10 grid coordinates [col(1-12), row(1-10)] for all 47 Prefectures of Japan
  const JAPAN_TILE_COORDS = [
    { pref: "北海道", short: "北海道", col: 11, row: 1, spanCol: 2, spanRow: 2, reg: "hokkaido" },
    { pref: "青森県", short: "青森", col: 11, row: 3, reg: "tohoku" },
    { pref: "秋田県", short: "秋田", col: 10, row: 4, reg: "tohoku" },
    { pref: "岩手県", short: "岩手", col: 11, row: 4, reg: "tohoku" },
    { pref: "山形県", short: "山形", col: 10, row: 5, reg: "tohoku" },
    { pref: "宮城県", short: "宮城", col: 11, row: 5, reg: "tohoku" },
    { pref: "福島県", short: "福島", col: 10, row: 6, spanCol: 2, reg: "tohoku" },

    { pref: "新潟県", short: "新潟", col: 9, row: 5, reg: "chubu" },
    { pref: "富山県", short: "富山", col: 8, row: 5, reg: "chubu" },
    { pref: "石川県", short: "石川", col: 7, row: 5, reg: "chubu" },
    { pref: "福井県", short: "福井", col: 7, row: 6, reg: "chubu" },
    { pref: "長野県", short: "長野", col: 9, row: 6, reg: "chubu" },
    { pref: "岐阜県", short: "岐阜", col: 8, row: 6, reg: "chubu" },
    { pref: "山梨県", short: "山梨", col: 9, row: 7, reg: "chubu" },
    { pref: "静岡県", short: "静岡", col: 9, row: 8, reg: "chubu" },
    { pref: "愛知県", short: "愛知", col: 8, row: 7, reg: "chubu" },

    { pref: "群馬県", short: "群馬", col: 10, row: 7, reg: "kanto" },
    { pref: "栃木県", short: "栃木", col: 11, row: 7, reg: "kanto" },
    { pref: "茨城県", short: "茨城", col: 12, row: 7, reg: "kanto" },
    { pref: "埼玉県", short: "埼玉", col: 10, row: 8, reg: "kanto" },
    { pref: "東京都", short: "東京", col: 11, row: 8, reg: "kanto" },
    { pref: "千葉県", short: "千葉", col: 12, row: 8, reg: "kanto" },
    { pref: "神奈川県", short: "神奈川", col: 10, row: 9, spanCol: 2, reg: "kanto" },

    { pref: "滋賀県", short: "滋賀", col: 7, row: 7, reg: "kinki" },
    { pref: "三重県", short: "三重", col: 8, row: 8, reg: "kinki" },
    { pref: "京都府", short: "京都", col: 6, row: 6, reg: "kinki" },
    { pref: "兵庫県", short: "兵庫", col: 5, row: 6, reg: "kinki" },
    { pref: "大阪府", short: "大阪", col: 6, row: 7, reg: "kinki" },
    { pref: "奈良県", short: "奈良", col: 7, row: 8, reg: "kinki" },
    { pref: "和歌山県", short: "和歌山", col: 6, row: 8, reg: "kinki" },

    { pref: "鳥取県", short: "鳥取", col: 4, row: 6, reg: "chugoku" },
    { pref: "島根県", short: "島根", col: 3, row: 6, reg: "chugoku" },
    { pref: "岡山県", short: "岡山", col: 4, row: 7, reg: "chugoku" },
    { pref: "広島県", short: "広島", col: 3, row: 7, reg: "chugoku" },
    { pref: "山口県", short: "山口", col: 2, row: 6, spanRow: 2, reg: "chugoku" },

    { pref: "香川県", short: "香川", col: 5, row: 8, reg: "shikoku" },
    { pref: "愛媛県", short: "愛媛", col: 4, row: 8, reg: "shikoku" },
    { pref: "徳島県", short: "徳島", col: 5, row: 9, reg: "shikoku" },
    { pref: "高知県", short: "高知", col: 4, row: 9, reg: "shikoku" },

    { pref: "福岡県", short: "福岡", col: 2, row: 8, reg: "kyushu_okinawa" },
    { pref: "佐賀県", short: "佐賀", col: 1, row: 8, reg: "kyushu_okinawa" },
    { pref: "長崎県", short: "長崎", col: 1, row: 9, reg: "kyushu_okinawa" },
    { pref: "大分県", short: "大分", col: 3, row: 8, reg: "kyushu_okinawa" },
    { pref: "熊本県", short: "熊本", col: 2, row: 9, reg: "kyushu_okinawa" },
    { pref: "宮崎県", short: "宮崎", col: 3, row: 9, reg: "kyushu_okinawa" },
    { pref: "鹿児島県", short: "鹿児島", col: 2, row: 10, spanCol: 2, reg: "kyushu_okinawa" },
    { pref: "沖縄県", short: "沖縄", col: 1, row: 10, reg: "kyushu_okinawa" },
  ];

  // -------------------------------------------------------------------------
  // Utilities
  // -------------------------------------------------------------------------
  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => Array.from(document.querySelectorAll(sel));

  function escapeHtml(str) {
    if (!str) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function formatNumber(n) {
    if (!n && n !== 0) return "-";
    if (n >= 10000) {
      return (n / 10000).toFixed(1).replace(/\.0$/, "") + "万";
    }
    return Number(n).toLocaleString("ja-JP");
  }

  function getSearchTokens(query) {
    if (!query || !query.trim()) return [];
    return query
      .trim()
      .split(/[\s　]+/)
      .filter(Boolean);
  }

  function highlightText(text, tokens) {
    const safe = escapeHtml(text || "");
    if (!tokens || tokens.length === 0) return safe;
    let out = safe;
    for (const rawTok of tokens) {
      const subTokens = rawTok.split("|").filter(Boolean);
      for (const tok of subTokens) {
        if (!tok) continue;
        const escapedTok = tok.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
        const re = new RegExp(`(${escapedTok})`, "gi");
        out = out.replace(re, '<mark class="hl">$1</mark>');
      }
    }
    return out;
  }

  function getMatchingSnippet(video, tokens) {
    if (!tokens || tokens.length === 0) {
      return video.excerpt || "";
    }
    const desc = video.description || "";
    for (const rawTok of tokens) {
      const subToks = rawTok.split("|").filter(Boolean);
      for (const tok of subToks) {
        const idx = desc.toLowerCase().indexOf(tok.toLowerCase());
        if (idx !== -1) {
          const start = Math.max(0, idx - 35);
          const end = Math.min(desc.length, idx + tok.length + 85);
          const prefix = start > 0 ? "…" : "";
          const suffix = end < desc.length ? "…" : "";
          return prefix + desc.slice(start, end).replace(/\s+/g, " ") + suffix;
        }
      }
    }
    return video.excerpt || "";
  }

  // -------------------------------------------------------------------------
  // User State Sync (Server + LocalStorage backup)
  // -------------------------------------------------------------------------
  const isStandalone = () => Boolean(window.__TOTTABI_DATASET__) || window.location.protocol === "file:";

  function applyServerUserState(rawState) {
    let localRaw = null;
    try {
      localRaw = JSON.parse(localStorage.getItem("tottabi_user_state") || "null");
    } catch (_) {}

    const base = rawState || {};
    const favs = new Set([...(base.favorites || []), ...((localRaw && localRaw.favorites) || [])]);
    const watched = new Set([...(base.watched || []), ...((localRaw && localRaw.watched) || [])]);
    const later = new Set([...(base.watch_later || []), ...((localRaw && localRaw.watch_later) || [])]);
    const notes = { ...(base.notes || {}), ...((localRaw && localRaw.notes) || {}) };

    userState.favorites = favs;
    userState.watched = watched;
    userState.watch_later = later;
    userState.notes = notes;
    saveLocalMirror();
    updateHeaderStats();
  }

  function saveLocalMirror() {
    try {
      localStorage.setItem(
        "tottabi_user_state",
        JSON.stringify({
          favorites: Array.from(userState.favorites),
          watched: Array.from(userState.watched),
          watch_later: Array.from(userState.watch_later),
          notes: userState.notes,
        })
      );
    } catch (_) {}
  }

  async function toggleVideoState(videoId, field, forceVal = null) {
    let newVal;
    if (field === "watched") {
      newVal = forceVal !== null ? forceVal : !userState.watched.has(videoId);
      if (newVal) userState.watched.add(videoId);
      else userState.watched.delete(videoId);
    } else if (field === "favorite") {
      newVal = forceVal !== null ? forceVal : !userState.favorites.has(videoId);
      if (newVal) userState.favorites.add(videoId);
      else userState.favorites.delete(videoId);
    } else if (field === "watch_later") {
      newVal = forceVal !== null ? forceVal : !userState.watch_later.has(videoId);
      if (newVal) userState.watch_later.add(videoId);
      else userState.watch_later.delete(videoId);
    }

    saveLocalMirror();
    updateHeaderStats();
    refreshCardDomState(videoId);
    if (uiState.modalVideoId === videoId) {
      updateModalButtons(videoId);
    }
    if (uiState.status !== "all" || uiState.currentView === "honeymoon") {
      renderCurrentView();
    }

    if (!isStandalone()) {
      try {
        await fetch("/api/user-state/video", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            video_id: videoId,
            [field]: newVal,
          }),
        });
      } catch (_) {}
    }
  }

  async function saveVideoNote(videoId, noteText) {
    const trimmed = (noteText || "").trim();
    if (trimmed) {
      userState.notes[videoId] = trimmed;
    } else {
      delete userState.notes[videoId];
    }
    saveLocalMirror();
    refreshCardDomState(videoId);
    if (!isStandalone()) {
      try {
        await fetch("/api/user-state/video", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ video_id: videoId, note: trimmed }),
        });
      } catch (_) {}
    }
  }

  async function bulkUpdateWatched(videoIds, watchedVal) {
    for (const vid of videoIds) {
      if (watchedVal) userState.watched.add(vid);
      else userState.watched.delete(vid);
    }
    saveLocalMirror();
    updateHeaderStats();
    renderCurrentView();
    if (!isStandalone()) {
      try {
        await fetch("/api/user-state/bulk", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ video_ids: videoIds, watched: watchedVal }),
        });
      } catch (_) {}
    }
  }

  function updateHeaderStats() {
    $("#statTotalVideos").textContent = `${allVideos.length.toLocaleString()}本`;
    const wCount = userState.watched.size;
    const pct = allVideos.length ? Math.round((wCount / allVideos.length) * 100) : 0;
    $("#statWatchedCount").textContent = `${wCount} (${pct}%)`;
    $("#statFavCount").textContent = `${userState.favorites.size}`;
    $("#statLaterCount").textContent = `${userState.watch_later.size}`;

    $("#quickFilterWatched").classList.toggle("active-stat", uiState.status === "watched");
    $("#quickFilterFav").classList.toggle("active-stat", uiState.status === "favorite");
    $("#quickFilterLater").classList.toggle("active-stat", uiState.status === "watch_later");
  }

  function refreshCardDomState(videoId) {
    const cards = $$(`.video-card[data-vid="${videoId}"]`);
    const isW = userState.watched.has(videoId);
    const isF = userState.favorites.has(videoId);
    const isL = userState.watch_later.has(videoId);
    for (const card of cards) {
      card.classList.toggle("is-watched", isW);
      const bW = card.querySelector('[data-action="watched"]');
      const bF = card.querySelector('[data-action="favorite"]');
      const bL = card.querySelector('[data-action="watch_later"]');
      if (bW) bW.classList.toggle("active-watched", isW);
      if (bF) bF.classList.toggle("active-fav", isF);
      if (bL) bL.classList.toggle("active-later", isL);
    }
  }

  // -------------------------------------------------------------------------
  // Filtering & Sorting Engine
  // -------------------------------------------------------------------------
  function filterVideos(videos, options = {}) {
    const tokens = getSearchTokens(uiState.searchQuery);
    const ignoreSeasonFilter = options.ignoreSeasonFilter || false;
    const overrideLocation = options.overrideLocation !== undefined ? options.overrideLocation : uiState.location;

    return videos.filter((v) => {
      // 1. Channel filter
      if (uiState.channel !== "all" && v.channel_key !== uiState.channel) return false;

      // 2. Shorts filter
      if (uiState.excludeShorts && v.video_type === "short") return false;

      // 3. User Status filter
      if (uiState.status === "unwatched" && userState.watched.has(v.id)) return false;
      if (uiState.status === "watched" && !userState.watched.has(v.id)) return false;
      if (uiState.status === "favorite" && !userState.favorites.has(v.id)) return false;
      if (uiState.status === "watch_later" && !userState.watch_later.has(v.id)) return false;
      if (uiState.status === "has_note" && !userState.notes[v.id]) return false;

      // 4. Category filter
      if (uiState.category !== "all" && v.category !== uiState.category) return false;

      // 5. Honeymoon Season filter
      if (!ignoreSeasonFilter && uiState.season !== "all") {
        if (uiState.season === "any_honeymoon") {
          if (!v.honeymoon_season_id) return false;
        } else if (v.honeymoon_season_id !== uiState.season) {
          return false;
        }
      }

      // 6. Location filter
      if (overrideLocation && overrideLocation !== "all") {
        if (overrideLocation === "scope:domestic") {
          if (v.location_scope !== "domestic" && v.location_scope !== "both") return false;
        } else if (overrideLocation === "scope:overseas") {
          if (v.location_scope !== "overseas" && v.location_scope !== "both") return false;
        } else if (overrideLocation.startsWith("region:")) {
          const rName = overrideLocation.slice(7);
          if (!v.japan_regions.includes(rName)) return false;
        } else if (overrideLocation.startsWith("pref:")) {
          const pName = overrideLocation.slice(5);
          if (!v.prefectures.includes(pName)) return false;
        } else if (overrideLocation.startsWith("country:")) {
          const cName = overrideLocation.slice(8);
          if (!v.overseas_countries.includes(cName)) return false;
        }
      }

      // 7. Year filter
      if (uiState.year !== "all" && v.publish_year !== uiState.year) return false;

      // 8. Duration filter
      if (uiState.duration !== "all") {
        const d = v.duration || 0;
        if (uiState.duration === "short_len" && d >= 600) return false;
        if (uiState.duration === "medium_len" && (d < 600 || d > 1500)) return false;
        if (uiState.duration === "long_len" && (d <= 1500 || d > 3600)) return false;
        if (uiState.duration === "compilation_len" && d <= 3600) return false;
      }

      // 9. Keyword search (AND across tokens, OR across '|' within a token)
      if (tokens.length > 0) {
        const noteStr = userState.notes[v.id] || "";
        const locStr = [...v.prefectures, ...v.japan_regions, ...v.overseas_countries, ...(v.playlist_titles || [])].join(" ");
        const haystack = uiState.searchDesc
          ? `${v.title} ${v.description} ${locStr} ${noteStr}`.toLowerCase()
          : `${v.title} ${locStr} ${noteStr}`.toLowerCase();

        for (const rawTok of tokens) {
          const orParts = rawTok.toLowerCase().split("|").filter(Boolean);
          const matchedOr = orParts.some((part) => haystack.includes(part));
          if (!matchedOr) return false;
        }
      }

      return true;
    });
  }

  function sortVideos(videos, customSort = null) {
    const mode = customSort || uiState.sortBy;
    const copy = [...videos];
    if (mode === "date_desc") {
      copy.sort((a, b) => (b.publish_date || "").localeCompare(a.publish_date || ""));
    } else if (mode === "date_asc") {
      copy.sort((a, b) => (a.publish_date || "9999").localeCompare(b.publish_date || "9999"));
    } else if (mode === "views_desc") {
      copy.sort((a, b) => (b.view_count || 0) - (a.view_count || 0));
    } else if (mode === "duration_desc") {
      copy.sort((a, b) => (b.duration || 0) - (a.duration || 0));
    } else if (mode === "duration_asc") {
      copy.sort((a, b) => (a.duration || 0) - (b.duration || 0));
    }
    return copy;
  }

  // -------------------------------------------------------------------------
  // Video Card Renderer
  // -------------------------------------------------------------------------
  function renderVideoCardHtml(v, tokens, showSeasonBadge = true) {
    const isW = userState.watched.has(v.id);
    const isF = userState.favorites.has(v.id);
    const isL = userState.watch_later.has(v.id);
    const note = userState.notes[v.id] || "";

    const titleHtml = highlightText(v.title, tokens);
    const snippetRaw = getMatchingSnippet(v, tokens);
    const snippetHtml = snippetRaw ? highlightText(snippetRaw, tokens) : "";

    const epBadge = v.season_episode_label
      ? `<span class="thumb-ep-badge">${escapeHtml(v.season_episode_label)}</span>`
      : v.video_type === "short"
      ? `<span class="thumb-ep-badge">Shorts</span>`
      : "";

    const watchedOverlay = isW ? `<span class="thumb-watched-badge">✓ 視聴済</span>` : "";

    const tagPills = [];
    if (showSeasonBadge && v.honeymoon_season_title) {
      tagPills.push(
        `<span class="tag-badge tag-hm" data-filter-season="${escapeHtml(v.honeymoon_season_id)}">🌏 ${escapeHtml(
          v.honeymoon_season_title
        )}</span>`
      );
    }
    for (const c of v.overseas_countries) {
      const flag = countryFlagMap.get(c) || "🌍";
      tagPills.push(
        `<span class="tag-badge tag-loc" data-filter-loc="country:${escapeHtml(c)}">${flag} ${escapeHtml(c)}</span>`
      );
    }
    for (const p of v.prefectures) {
      tagPills.push(
        `<span class="tag-badge tag-loc" data-filter-loc="pref:${escapeHtml(p)}">📍 ${escapeHtml(p)}</span>`
      );
    }
    if (v.prefectures.length === 0 && v.japan_regions.length > 0) {
      for (const r of v.japan_regions) {
        tagPills.push(
          `<span class="tag-badge tag-loc" data-filter-loc="region:${escapeHtml(r)}">🗾 ${escapeHtml(r)}</span>`
        );
      }
    }
    if (v.category && !v.honeymoon_season_title) {
      tagPills.push(
        `<span class="tag-badge" data-filter-cat="${escapeHtml(v.category)}">${escapeHtml(v.category)}</span>`
      );
    }

    return `
      <article class="video-card ${isW ? "is-watched" : ""}" data-vid="${escapeHtml(v.id)}">
        <div class="thumb-wrap" data-open-modal="${escapeHtml(v.id)}">
          <img class="thumb-img" src="${escapeHtml(v.thumbnail)}" alt="" loading="lazy" />
          ${epBadge}
          ${watchedOverlay}
          <span class="thumb-duration">${escapeHtml(v.duration_str)}</span>
        </div>
        <div class="card-body">
          <div class="card-main-info">
            <div class="card-meta-top">
              <span class="channel-tag ${escapeHtml(v.channel_key)}">${escapeHtml(v.channel_name)}</span>
              <span>📅 ${escapeHtml(v.publish_date || "-")}</span>
              <span>👁 ${formatNumber(v.view_count)}回</span>
            </div>
            <h4 class="card-title" data-open-modal="${escapeHtml(v.id)}">${titleHtml}</h4>
          </div>
          ${snippetHtml ? `<div class="card-excerpt">${snippetHtml}</div>` : ""}
          ${note ? `<div class="card-note-preview">📝 ${highlightText(note, tokens)}</div>` : ""}
          <div class="card-tags">${tagPills.join("")}</div>
          <div class="card-actions">
            <div class="state-btns">
              <button class="action-icon-btn ${isW ? "active-watched" : ""}" data-action="watched" data-vid="${escapeHtml(
      v.id
    )}" title="視聴済みチェック">✓ 視聴済</button>
              <button class="action-icon-btn ${isF ? "active-fav" : ""}" data-action="favorite" data-vid="${escapeHtml(
      v.id
    )}" title="お気に入り">★</button>
              <button class="action-icon-btn ${isL ? "active-later" : ""}" data-action="watch_later" data-vid="${escapeHtml(
      v.id
    )}" title="後で見る">🕒</button>
            </div>
            <div style="display:flex;gap:6px;align-items:center;">
              <button class="action-icon-btn" data-open-modal="${escapeHtml(v.id)}" title="概要欄・詳細を見る">📖 詳細</button>
              <a class="action-icon-btn" href="${escapeHtml(v.url)}" target="_blank" rel="noopener noreferrer" title="YouTubeで開く" style="text-decoration:none;">▶ YouTube ↗</a>
            </div>
          </div>
        </div>
      </article>
    `;
  }

  // -------------------------------------------------------------------------
  // Active Filter Chips & Summary Bar
  // -------------------------------------------------------------------------
  function renderActiveFilterChips(filteredVideos) {
    $("#filteredCount").textContent = filteredVideos.length.toLocaleString();
    const tottabiCnt = filteredVideos.filter((v) => v.channel_key === "tottabi").length;
    const biyoriCnt = filteredVideos.filter((v) => v.channel_key === "tottabi_biyori").length;
    const watchedCnt = filteredVideos.filter((v) => userState.watched.has(v.id)).length;
    $("#filteredSubInfo").textContent = `（とったび: ${tottabiCnt}本 / とったび日和: ${biyoriCnt}本 ｜ 視聴済み: ${watchedCnt}本）`;

    const chips = [];
    if (uiState.searchQuery.trim()) {
      chips.push({ label: `🔍 "${uiState.searchQuery.trim()}"`, clear: () => { $("#searchInput").value = ""; uiState.searchQuery = ""; $("#btnSearchClear").classList.add("hidden"); } });
    }
    if (uiState.channel !== "all") {
      const chLabel = uiState.channel === "tottabi" ? "🚐 とったび" : "☀️ とったび日和";
      chips.push({ label: chLabel, clear: () => setChannelFilter("all") });
    }
    if (uiState.status !== "all") {
      const stLabels = { unwatched: "👀 未視聴", watched: "✅ 視聴済み", favorite: "★ お気に入り", watch_later: "🕒 後で見る", has_note: "📝 メモあり" };
      chips.push({ label: stLabels[uiState.status], clear: () => { uiState.status = "all"; $("#filterStatus").value = "all"; } });
    }
    if (uiState.category !== "all") {
      chips.push({ label: `📂 ${uiState.category}`, clear: () => { uiState.category = "all"; $("#filterCategory").value = "all"; } });
    }
    if (uiState.season !== "all") {
      const hm = dataset.honeymoon_seasons.find((s) => s.id === uiState.season);
      chips.push({ label: `🌏 ${hm ? hm.title : "ハネムーン"}`, clear: () => { uiState.season = "all"; $("#filterSeason").value = "all"; } });
    }
    if (uiState.location !== "all") {
      chips.push({ label: `📍 ${uiState.location.replace(/^(pref|region|country|scope):/, "")}`, clear: () => { uiState.location = "all"; $("#filterLocation").value = "all"; } });
    }
    if (uiState.year !== "all") {
      chips.push({ label: `📅 ${uiState.year}年`, clear: () => { uiState.year = "all"; $("#filterYear").value = "all"; } });
    }
    if (uiState.duration !== "all") {
      chips.push({ label: `⏱ 長さ指定`, clear: () => { uiState.duration = "all"; $("#filterDuration").value = "all"; } });
    }
    if (uiState.excludeShorts) {
      chips.push({ label: `Shorts除外`, clear: () => { uiState.excludeShorts = false; $("#chkExcludeShorts").checked = false; } });
    }

    const container = $("#activeChips");
    container.innerHTML = chips
      .map((c, i) => `<span class="filter-chip" data-chip-idx="${i}">${escapeHtml(c.label)} ✕</span>`)
      .join("");

    container.querySelectorAll(".filter-chip").forEach((el) => {
      el.addEventListener("click", () => {
        const idx = Number(el.dataset.chipIdx);
        if (chips[idx]) {
          chips[idx].clear();
          updateHeaderStats();
          renderCurrentView();
        }
      });
    });
  }

  // -------------------------------------------------------------------------
  // View 1: Honeymoon Seasons View
  // -------------------------------------------------------------------------
  function renderHoneymoonView() {
    const tokens = getSearchTokens(uiState.searchQuery);
    const seasons = dataset.honeymoon_seasons || [];

    // Sticky Season Switcher Bar
    const jumpBar = $("#seasonJumpBar");
    const isAllSeasons = uiState.season === "all" || uiState.season === "any_honeymoon";
    const allPillHtml = `
      <button class="season-jump-pill ${isAllSeasons ? "active" : ""}" data-select-season="all">
        <span>🌏 全シーズン表示</span>
      </button>
    `;
    jumpBar.innerHTML =
      allPillHtml +
      seasons
        .map((s) => {
          const isAct = uiState.season === s.id;
          return `
            <button class="season-jump-pill ${isAct ? "active" : ""}" data-select-season="${escapeHtml(s.id)}">
              <span style="color:${escapeHtml(s.badge_color)}">●</span>
              <span>${escapeHtml(s.title)}</span>
              <span class="tab-badge">${s.video_count}本</span>
            </button>
          `;
        })
        .join("");

    jumpBar.querySelectorAll(".season-jump-pill").forEach((btn) => {
      btn.addEventListener("click", () => {
        const chosen = btn.dataset.selectSeason;
        if (chosen === "all" || uiState.season === chosen) {
          uiState.season = "all";
        } else {
          uiState.season = chosen;
        }
        $("#filterSeason").value = uiState.season;
        renderHoneymoonView();
        const anchor = document.getElementById("honeymoonSeasonsContainer");
        if (anchor) {
          const panelHeight = ($(".search-panel") && $(".search-panel").offsetHeight) || 120;
          const topY = anchor.getBoundingClientRect().top + window.scrollY - panelHeight - 12;
          if (window.scrollY > topY) {
            window.scrollTo({ top: Math.max(0, topY), behavior: "smooth" });
          }
        }
      });
    });

    const container = $("#honeymoonSeasonsContainer");
    const htmlBlocks = [];
    let totalMatchingAcrossSeasons = 0;

    for (const s of seasons) {
      if (uiState.season !== "all" && uiState.season !== "any_honeymoon" && uiState.season !== s.id) {
        continue;
      }

      let sVideos = s.video_ids.map((id) => videoMap.get(id)).filter(Boolean);
      if (!uiState.hmIncludeSub) {
        sVideos = sVideos.filter((v) => v.channel_key === "tottabi");
      }

      const filtered = filterVideos(sVideos, { ignoreSeasonFilter: true });
      if (filtered.length === 0) continue;

      totalMatchingAcrossSeasons += filtered.length;

      const ordered = uiState.hmChronological && s.id !== "hm_extra"
        ? [...filtered].sort((a, b) => (a.publish_date || "").localeCompare(b.publish_date || ""))
        : sortVideos(filtered);

      const watchedCount = ordered.filter((v) => userState.watched.has(v.id)).length;
      const pct = ordered.length ? Math.round((watchedCount / ordered.length) * 100) : 0;
      const allWatched = ordered.length > 0 && watchedCount === ordered.length;

      const countryChips = (s.countries || [])
        .map((c) => {
          const flag = countryFlagMap.get(c) || "🌍";
          const isAct = uiState.location === `country:${c}`;
          return `<span class="country-chip ${isAct ? "active" : ""}" data-filter-loc="country:${escapeHtml(
            c
          )}">${flag} ${escapeHtml(c)}</span>`;
        })
        .join("");

      const cardsHtml = ordered.map((v) => renderVideoCardHtml(v, tokens, false)).join("");
      const layoutClass = uiState.layout === "list" ? "videos-list" : "videos-grid";

      htmlBlocks.push(`
        <div class="season-card" id="season-card-${escapeHtml(s.id)}">
          <div class="season-card-header">
            <div class="season-header-top">
              <div class="season-title-group">
                <div class="season-title-row">
                  <span class="season-badge" style="background:${escapeHtml(s.badge_color)}">${escapeHtml(
        s.title
      )}</span>
                  <h3>${escapeHtml(s.subtitle)}</h3>
                  <span class="season-period">🗓 ${escapeHtml(s.period)}</span>
                </div>
                <p class="season-desc">${escapeHtml(s.description)}</p>
              </div>
              <div class="season-header-right">
                <div class="season-progress-wrap">
                  <div class="season-progress-text">
                    <span>視聴進捗: <strong>${watchedCount} / ${ordered.length}本</strong> (${pct}%)</span>
                    <span>本編:${ordered.filter((x) => x.channel_key === "tottabi").length} / 日和:${
        ordered.filter((x) => x.channel_key === "tottabi_biyori").length
      }</span>
                  </div>
                  <div class="season-progress-bar">
                    <div class="season-progress-fill" style="width:${pct}%"></div>
                  </div>
                </div>
                <button class="btn btn-sm btn-secondary" data-bulk-season="${escapeHtml(s.id)}" data-bulk-val="${
        allWatched ? "false" : "true"
      }">
                  ${allWatched ? "↩ このシーズンの視聴済みを解除" : "✅ このシーズンを一括視聴済みにする"}
                </button>
              </div>
            </div>
            <div class="season-countries-row">
              <div class="season-countries-list">
                <span style="font-size:0.78rem;color:var(--text-muted);align-self:center;">訪問国で絞り込み:</span>
                ${countryChips}
              </div>
            </div>
          </div>
          <div class="season-body">
            <div class="${layoutClass}">
              ${cardsHtml}
            </div>
          </div>
        </div>
      `);
    }

    if (htmlBlocks.length === 0) {
      container.innerHTML = `<div class="map-panel" style="text-align:center;padding:40px;">条件に一致するハネムーン動画が見つかりませんでした。「全動画一覧・検索」タブに切り替えるか、検索条件を緩めてみてください。</div>`;
    } else {
      container.innerHTML = htmlBlocks.join("");
    }

    // Bind bulk season watched buttons
    container.querySelectorAll("[data-bulk-season]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const sid = btn.dataset.bulkSeason;
        const val = btn.dataset.bulkVal === "true";
        const sObj = seasons.find((x) => x.id === sid);
        if (sObj) {
          bulkUpdateWatched(sObj.video_ids, val);
        }
      });
    });

    const allFiltered = filterVideos(allVideos.filter((v) => v.honeymoon_season_id));
    renderActiveFilterChips(allFiltered);
  }

  // -------------------------------------------------------------------------
  // View 2: Interactive Japan 47 Prefectures & World Map View
  // -------------------------------------------------------------------------
  function renderMapView() {
    $("#mapJapanContainer").classList.toggle("hidden", uiState.mapMode !== "japan");
    $("#mapWorldContainer").classList.toggle("hidden", uiState.mapMode !== "world");
    $$(".subtab-btn").forEach((b) => b.classList.toggle("active", b.dataset.mapmode === uiState.mapMode));

    // Calculate live counts for each prefecture, region, and overseas country under current base filters (ignoring location)
    const baseFiltered = filterVideos(allVideos, { overrideLocation: "all" });
    const prefCounts = new Map();
    const regionCounts = new Map();
    const countryCounts = new Map();

    for (const v of baseFiltered) {
      for (const p of v.prefectures) prefCounts.set(p, (prefCounts.get(p) || 0) + 1);
      for (const r of v.japan_regions) regionCounts.set(r, (regionCounts.get(r) || 0) + 1);
      for (const c of v.overseas_countries) countryCounts.set(c, (countryCounts.get(c) || 0) + 1);
    }

    if (uiState.mapMode === "japan") {
      // 1. Render Tile Map
      const tileMap = $("#japanTileMap");
      tileMap.innerHTML = JAPAN_TILE_COORDS.map((t) => {
        const cnt = prefCounts.get(t.pref) || 0;
        const locKey = `pref:${t.pref}`;
        const isSelected = uiState.location === locKey;
        const bgAlpha = cnt >= 12 ? 0.55 : cnt >= 6 ? 0.35 : cnt >= 1 ? 0.18 : 0.05;
        const bgStyle = isSelected
          ? ""
          : cnt > 0
          ? `background: rgba(14, 165, 233, ${bgAlpha}); border-color: rgba(56, 189, 248, 0.45);`
          : `opacity: 0.45;`;
        const gridStyle = `grid-column: ${t.col} / span ${t.spanCol || 1}; grid-row: ${t.row} / span ${
          t.spanRow || 1
        }; ${bgStyle}`;

        return `
          <div class="pref-tile ${isSelected ? "selected" : ""}" style="${gridStyle}" data-map-loc="${escapeHtml(
          locKey
        )}" title="${escapeHtml(t.pref)}: ${cnt}本">
            <span class="pref-name">${escapeHtml(t.short)}</span>
            <span class="pref-count">${cnt}本</span>
          </div>
        `;
      }).join("");

      // 2. Render Region Sidebar
      const regList = $("#japanRegionList");
      regList.innerHTML = (dataset.japan_regions || [])
        .map((reg) => {
          const rCnt = regionCounts.get(reg.name) || 0;
          const rKey = `region:${reg.name}`;
          const prefsHtml = reg.prefectures
            .map((p) => {
              const pCnt = prefCounts.get(p.name) || 0;
              const pKey = `pref:${p.name}`;
              const isAct = uiState.location === pKey;
              return `<span class="country-chip ${isAct ? "active" : ""}" data-map-loc="${escapeHtml(
                pKey
              )}">${escapeHtml(p.name.replace(/[都府県]$/, ""))} <strong>${pCnt}</strong></span>`;
            })
            .join("");

          return `
            <div class="region-box">
              <div class="region-box-header" data-map-loc="${escapeHtml(rKey)}">
                <span>🗾 ${escapeHtml(reg.name)}地方</span>
                <span class="tab-badge">${rCnt}本</span>
              </div>
              <div class="region-prefs-wrap">${prefsHtml}</div>
            </div>
          `;
        })
        .join("");
    } else {
      // Render World Countries by Region
      const worldContainer = $("#worldRegionsContainer");
      const countriesByReg = new Map();
      for (const c of dataset.overseas_countries || []) {
        if (!countriesByReg.has(c.region)) countriesByReg.set(c.region, []);
        countriesByReg.get(c.region).push(c);
      }

      const regBlocks = [];
      for (const [regName, cList] of countriesByReg.entries()) {
        const cards = cList
          .map((c) => {
            const cnt = countryCounts.get(c.name) || 0;
            const cKey = `country:${c.name}`;
            const isAct = uiState.location === cKey;
            return `
              <div class="world-country-card ${isAct ? "active" : ""}" data-map-loc="${escapeHtml(cKey)}">
                <div class="wc-left">
                  <span class="wc-flag">${escapeHtml(c.flag)}</span>
                  <span>${escapeHtml(c.name)}</span>
                </div>
                <span class="wc-count">${cnt}本</span>
              </div>
            `;
          })
          .join("");

        regBlocks.push(`
          <div class="world-region-group">
            <h4>🌐 ${escapeHtml(regName)}</h4>
            <div class="world-countries-grid">${cards}</div>
          </div>
        `);
      }
      worldContainer.innerHTML = regBlocks.join("");
    }

    // Bind map location clicks
    $$("[data-map-loc]").forEach((el) => {
      el.addEventListener("click", () => {
        const loc = el.dataset.mapLoc;
        uiState.location = uiState.location === loc ? "all" : loc;
        $("#filterLocation").value = uiState.location;
        renderMapView();
        document.getElementById("mapResultsSection").scrollIntoView({ behavior: "smooth", block: "nearest" });
      });
    });

    // Render filtered videos below the map
    const effectiveLoc =
      uiState.location !== "all"
        ? uiState.location
        : uiState.mapMode === "japan"
        ? "scope:domestic"
        : "scope:overseas";
    const mapVideos = sortVideos(filterVideos(allVideos, { overrideLocation: effectiveLoc }));
    const tokens = getSearchTokens(uiState.searchQuery);

    const locTitle =
      uiState.location !== "all"
        ? `📍 「${uiState.location.replace(/^(pref|region|country|scope):/, "")}」の動画一覧（${mapVideos.length}本）`
        : uiState.mapMode === "japan"
        ? `🗾 国内旅・47都道府県の動画一覧（${mapVideos.length}本）※上の地図をクリックして都道府県で絞り込めます`
        : `🌍 海外旅・世界各国の動画一覧（${mapVideos.length}本）※上の国カードをクリックして国別で絞り込めます`;

    $("#mapResultsTitle").textContent = locTitle;
    const mapContainer = $("#mapVideosContainer");
    mapContainer.className = uiState.layout === "list" ? "videos-list" : "videos-grid";
    mapContainer.innerHTML = mapVideos
      .slice(0, 120)
      .map((v) => renderVideoCardHtml(v, tokens, true))
      .join("");

    renderActiveFilterChips(mapVideos);
  }

  // -------------------------------------------------------------------------
  // View 3: Playlists & Series View
  // -------------------------------------------------------------------------
  function renderPlaylistsView() {
    const tokens = getSearchTokens(uiState.searchQuery);
    const playlists = dataset.playlists || [];
    const container = $("#playlistsContainer");
    const blocks = [];

    for (const pl of playlists) {
      const plVideos = pl.video_ids.map((id) => videoMap.get(id)).filter(Boolean);
      const filtered = filterVideos(plVideos);
      if (filtered.length === 0) continue;

      const watchedCnt = filtered.filter((v) => userState.watched.has(v.id)).length;
      const pct = filtered.length ? Math.round((watchedCnt / filtered.length) * 100) : 0;
      const isOpen = uiState.openPlaylists.has(pl.id) || tokens.length > 0 || playlists.indexOf(pl) < 3;

      const cardsHtml = isOpen
        ? `<div class="playlist-acc-body"><div class="${
            uiState.layout === "list" ? "videos-list" : "videos-grid"
          }">${filtered.map((v) => renderVideoCardHtml(v, tokens, true)).join("")}</div></div>`
        : "";

      blocks.push(`
        <div class="playlist-accordion" data-pl-id="${escapeHtml(pl.id)}">
          <div class="playlist-acc-header" data-toggle-pl="${escapeHtml(pl.id)}">
            <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;">
              <span class="channel-tag ${escapeHtml(pl.channel_key)}">${escapeHtml(pl.channel_name)}</span>
              <strong>${escapeHtml(pl.title)}</strong>
              <span class="tab-badge">${filtered.length}本</span>
            </div>
            <div style="display:flex;align-items:center;gap:14px;">
              <span style="font-size:0.78rem;color:var(--text-sub);">視聴済: ${watchedCnt}/${filtered.length} (${pct}%)</span>
              <span>${isOpen ? "▲ 閉じる" : "▼ 展開する"}</span>
            </div>
          </div>
          ${cardsHtml}
        </div>
      `);
    }

    container.innerHTML =
      blocks.length > 0
        ? blocks.join("")
        : `<div class="map-panel" style="text-align:center;padding:40px;">条件に一致する再生リストがありません。</div>`;

    container.querySelectorAll("[data-toggle-pl]").forEach((hdr) => {
      hdr.addEventListener("click", () => {
        const pid = hdr.dataset.togglePl;
        if (uiState.openPlaylists.has(pid)) uiState.openPlaylists.delete(pid);
        else uiState.openPlaylists.add(pid);
        renderPlaylistsView();
      });
    });

    renderActiveFilterChips(filterVideos(allVideos));
  }

  // -------------------------------------------------------------------------
  // View 4: All Videos Flat / Timeline View
  // -------------------------------------------------------------------------
  function renderAllVideosView() {
    const tokens = getSearchTokens(uiState.searchQuery);
    const filtered = sortVideos(filterVideos(allVideos));
    renderActiveFilterChips(filtered);

    const container = $("#allVideosContainer");
    const visible = filtered.slice(0, uiState.allViewLimit);

    if (visible.length === 0) {
      container.innerHTML = `<div class="map-panel" style="text-align:center;padding:48px;">条件に一致する動画が見つかりませんでした。検索ワードやフィルタを変更してみてください。</div>`;
      $("#loadMoreWrap").classList.add("hidden");
      return;
    }

    if (uiState.layout === "timeline") {
      // Group by YYYY-MM
      const byMonth = new Map();
      for (const v of visible) {
        const ym = v.publish_month || "不明";
        if (!byMonth.has(ym)) byMonth.set(ym, []);
        byMonth.get(ym).push(v);
      }
      const monthBlocks = [];
      for (const [ym, vList] of byMonth.entries()) {
        const label = ym !== "不明" ? `${ym.slice(0, 4)}年 ${Number(ym.slice(5, 7))}月` : "公開日不明";
        monthBlocks.push(`
          <div class="timeline-month-group">
            <div class="timeline-month-header">
              <span>📅 ${escapeHtml(label)}</span>
              <span>${vList.length}本</span>
            </div>
            <div class="videos-grid">
              ${vList.map((v) => renderVideoCardHtml(v, tokens, true)).join("")}
            </div>
          </div>
        `);
      }
      container.innerHTML = monthBlocks.join("");
    } else {
      const cls = uiState.layout === "list" ? "videos-list" : "videos-grid";
      container.innerHTML = `<div class="${cls}">${visible
        .map((v) => renderVideoCardHtml(v, tokens, true))
        .join("")}</div>`;
    }

    const hasMore = filtered.length > uiState.allViewLimit;
    $("#loadMoreWrap").classList.toggle("hidden", !hasMore);
    if (hasMore) {
      $("#btnLoadMore").textContent = `さらに表示する（残り ${filtered.length - uiState.allViewLimit} 本）`;
    }
  }

  // -------------------------------------------------------------------------
  // Main Render Dispatcher
  // -------------------------------------------------------------------------
  function renderCurrentView() {
    if (!dataset) return;

    $$(".view-tab").forEach((t) => t.classList.toggle("active", t.dataset.view === uiState.currentView));
    $("#viewHoneymoon").classList.toggle("hidden", uiState.currentView !== "honeymoon");
    $("#viewMap").classList.toggle("hidden", uiState.currentView !== "map");
    $("#viewPlaylists").classList.toggle("hidden", uiState.currentView !== "playlists");
    $("#viewAll").classList.toggle("hidden", uiState.currentView !== "all");
    if ($("#seasonJumpBar")) {
      $("#seasonJumpBar").classList.toggle("hidden", uiState.currentView !== "honeymoon");
    }

    if (uiState.currentView === "honeymoon") {
      renderHoneymoonView();
    } else if (uiState.currentView === "map") {
      renderMapView();
    } else if (uiState.currentView === "playlists") {
      renderPlaylistsView();
    } else {
      renderAllVideosView();
    }
  }

  function switchView(viewName) {
    uiState.currentView = viewName;
    renderCurrentView();
  }

  function setChannelFilter(ch) {
    uiState.channel = ch;
    $$("#channelFilterGroup .seg-btn").forEach((b) => b.classList.toggle("active", b.dataset.channel === ch));
    renderCurrentView();
  }

  // -------------------------------------------------------------------------
  // Video Detail & Player Modal
  // -------------------------------------------------------------------------
  function openVideoModal(videoId) {
    const v = videoMap.get(videoId);
    if (!v) return;
    uiState.modalVideoId = videoId;

    // Determine context list for Prev/Next navigation
    const visibleCards = $$(".view-section:not(.hidden) .video-card[data-vid]");
    uiState.modalContextList = visibleCards.map((c) => c.dataset.vid);

    $("#modalChannelBadge").textContent = v.channel_name;
    $("#modalChannelBadge").className = `channel-tag ${v.channel_key}`;
    $("#modalVideoTitle").textContent = v.title;
    $("#modalYoutubeLink").href = v.url;

    // In file:// mode, YouTube iframe embeds often fail with Error 153 due to missing HTTP Referer/Origin.
    // Provide a rich clickable thumbnail player that opens YouTube directly, plus an optional embed toggle.
    if (window.location.protocol === "file:") {
      $("#modalPlayerBox").innerHTML = `
        <div style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;background:#000;overflow:hidden;">
          <img src="${escapeHtml(v.thumbnail)}" alt="" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;opacity:0.55;filter:blur(1px);" />
          <div style="position:relative;z-index:2;display:flex;flex-direction:column;align-items:center;gap:12px;text-align:center;padding:20px;">
            <a href="${escapeHtml(v.url)}" target="_blank" rel="noopener noreferrer" class="btn btn-primary" style="font-size:1.05rem;padding:12px 24px;border-radius:999px;box-shadow:0 8px 25px rgba(0,0,0,0.6);">
              ▶ YouTubeで動画を再生する ↗
            </a>
            <button id="btnTryInlineEmbed" class="btn btn-sm btn-secondary" style="background:rgba(15,23,42,0.85);color:#e2e8f0;border-color:rgba(255,255,255,0.25);">
              埋め込みプレイヤーを試す
            </button>
          </div>
        </div>
      `;
      const btnTry = $("#btnTryInlineEmbed");
      if (btnTry) {
        btnTry.addEventListener("click", () => {
          $("#modalPlayerBox").innerHTML = `
            <iframe
              id="ytIframe"
              src="https://www.youtube-nocookie.com/embed/${encodeURIComponent(v.id)}?autoplay=1&rel=0"
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              allowfullscreen
            ></iframe>
          `;
        });
      }
    } else {
      $("#modalPlayerBox").innerHTML = `
        <iframe
          id="ytIframe"
          src="https://www.youtube.com/embed/${encodeURIComponent(v.id)}?autoplay=1&rel=0"
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
          allowfullscreen
        ></iframe>
      `;
    }

    $("#modalMetaRow").innerHTML = `
      <span>📅 公開日: <strong>${escapeHtml(v.publish_date || "-")}</strong></span>
      <span>👁 再生回数: <strong>${Number(v.view_count || 0).toLocaleString()}回</strong></span>
      <span>⏱ 長さ: <strong>${escapeHtml(v.duration_str)}</strong></span>
    `;

    const tags = [];
    if (v.honeymoon_season_title) {
      tags.push(`<span class="tag-badge tag-hm">🌏 ${escapeHtml(v.honeymoon_season_title)}</span>`);
    }
    for (const c of v.overseas_countries) {
      tags.push(`<span class="tag-badge tag-loc">${countryFlagMap.get(c) || "🌍"} ${escapeHtml(c)}</span>`);
    }
    for (const p of v.prefectures) {
      tags.push(`<span class="tag-badge tag-loc">📍 ${escapeHtml(p)}</span>`);
    }
    for (const pl of v.playlists || []) {
      tags.push(`<span class="tag-badge">📚 ${escapeHtml(pl.title)} (#${pl.position})</span>`);
    }
    $("#modalTagsRow").innerHTML = tags.join("");

    // Format description with clickable links and timestamps
    const descEscaped = escapeHtml(v.description || "（概要欄なし）")
      .replace(/(https?:\/\/[^\s<]+)/g, '<a href="$1" target="_blank" rel="noopener noreferrer" style="color:var(--accent-primary)">$1</a>')
      .replace(/\b(?:(\d{1,2}):)?([0-5]?\d):([0-5]\d)\b/g, (match, h, m, s) => {
        const totalSec = (Number(h || 0) * 3600) + (Number(m) * 60) + Number(s);
        return `<a href="https://www.youtube.com/watch?v=${encodeURIComponent(v.id)}&t=${totalSec}s" target="_blank" rel="noopener noreferrer" class="seek-link" data-seek="${totalSec}" style="color:var(--accent-primary);font-weight:700;">${match}</a>`;
      });

    $("#modalDescription").innerHTML = descEscaped;
    $("#modalDescription").querySelectorAll(".seek-link").forEach((a) => {
      a.addEventListener("click", (e) => {
        const iframe = $("#ytIframe");
        if (iframe) {
          e.preventDefault();
          const sec = Number(a.dataset.seek || 0);
          iframe.src = `https://www.youtube.com/embed/${encodeURIComponent(v.id)}?autoplay=1&start=${sec}&rel=0`;
        }
      });
    });

    $("#modalNoteInput").value = userState.notes[v.id] || "";
    updateModalButtons(v.id);

    const idx = uiState.modalContextList.indexOf(v.id);
    $("#modalBtnPrev").disabled = idx <= 0;
    $("#modalBtnNext").disabled = idx === -1 || idx >= uiState.modalContextList.length - 1;

    $("#videoModal").classList.remove("hidden");
  }

  function updateModalButtons(videoId) {
    const isW = userState.watched.has(videoId);
    const isF = userState.favorites.has(videoId);
    const isL = userState.watch_later.has(videoId);
    const bW = $("#modalBtnWatched");
    const bF = $("#modalBtnFav");
    const bL = $("#modalBtnLater");
    bW.classList.toggle("active-watched", isW);
    bW.textContent = isW ? "✅ 視聴済み (解除)" : "✅ 視聴済みにする";
    bF.classList.toggle("active-fav", isF);
    bF.textContent = isF ? "★ お気に入り済" : "★ お気に入り";
    bL.classList.toggle("active-later", isL);
    bL.textContent = isL ? "🕒 後で見る済" : "🕒 後で見る";
  }

  function closeVideoModal() {
    $("#videoModal").classList.add("hidden");
    $("#modalPlayerBox").innerHTML = "";
    uiState.modalVideoId = null;
  }

  // -------------------------------------------------------------------------
  // Populate Dropdowns & Initial Setup
  // -------------------------------------------------------------------------
  function populateFilterDropdowns() {
    // 1. Categories
    const catSelect = $("#filterCategory");
    catSelect.innerHTML =
      `<option value="all">全カテゴリ</option>` +
      (dataset.categories || [])
        .map((c) => `<option value="${escapeHtml(c.name)}">${escapeHtml(c.name)} (${c.count})</option>`)
        .join("");

    // 2. Honeymoon Seasons
    const seasonSelect = $("#filterSeason");
    seasonSelect.innerHTML =
      `<option value="all">全シーズン / 指定なし</option>` +
      `<option value="any_honeymoon">🌏 ハネムーン・海外シリーズすべて</option>` +
      (dataset.honeymoon_seasons || [])
        .map((s) => `<option value="${escapeHtml(s.id)}">${escapeHtml(s.title)}: ${escapeHtml(s.subtitle)} (${s.video_count})</option>`)
        .join("");

    // 3. Locations (Scope + Overseas Countries + Japan Regions & Prefectures)
    const locSelect = $("#filterLocation");
    const locOptions = [
      `<option value="all">すべての地域</option>`,
      `<option value="scope:domestic">🗾 国内（日本）すべて</option>`,
      `<option value="scope:overseas">🌍 海外すべて</option>`,
    ];

    if (dataset.overseas_countries && dataset.overseas_countries.length > 0) {
      locOptions.push(`<optgroup label="🌍 海外（国・地域別）">`);
      for (const c of dataset.overseas_countries) {
        locOptions.push(
          `<option value="country:${escapeHtml(c.name)}">${escapeHtml(c.flag)} ${escapeHtml(c.name)} (${c.count})</option>`
        );
      }
      locOptions.push(`</optgroup>`);
    }

    for (const reg of dataset.japan_regions || []) {
      locOptions.push(`<optgroup label="🗾 ${escapeHtml(reg.name)}地方 (${reg.count}本)">`);
      locOptions.push(`<option value="region:${escapeHtml(reg.name)}">【${escapeHtml(reg.name)}地方すべて】 (${reg.count})</option>`);
      for (const p of reg.prefectures) {
        locOptions.push(`<option value="pref:${escapeHtml(p.name)}">　📍 ${escapeHtml(p.name)} (${p.count})</option>`);
      }
      locOptions.push(`</optgroup>`);
    }
    locSelect.innerHTML = locOptions.join("");

    // 4. Years
    const yearSelect = $("#filterYear");
    yearSelect.innerHTML =
      `<option value="all">全期間</option>` +
      (dataset.years || [])
        .map((y) => `<option value="${escapeHtml(y.year)}">${escapeHtml(y.year)}年 (${y.count}本)</option>`)
        .join("");

    // Update Tab Badges
    const hmTotal = allVideos.filter((v) => v.honeymoon_season_id).length;
    $("#tabBadgeHoneymoon").textContent = `${hmTotal}本`;
    $("#tabBadgePlaylists").textContent = `${(dataset.playlists || []).length}件`;
    $("#tabBadgeAll").textContent = `${allVideos.length}本`;

    if (dataset.updated_at) {
      try {
        $("#lastUpdatedText").textContent = new Date(dataset.updated_at).toLocaleString("ja-JP");
      } catch (_) {
        $("#lastUpdatedText").textContent = dataset.updated_at;
      }
    }
  }

  // -------------------------------------------------------------------------
  // Event Listeners
  // -------------------------------------------------------------------------
  function bindEvents() {
    // View tabs
    $$(".view-tab").forEach((btn) => {
      btn.addEventListener("click", () => switchView(btn.dataset.view));
    });

    // Map mode subtabs
    $$(".subtab-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        uiState.mapMode = btn.dataset.mapmode;
        uiState.location = "all";
        $("#filterLocation").value = "all";
        renderMapView();
      });
    });

    $("#btnClearMapSelection").addEventListener("click", () => {
      uiState.location = "all";
      $("#filterLocation").value = "all";
      renderMapView();
    });
    $("#btnClearWorldSelection").addEventListener("click", () => {
      uiState.location = "all";
      $("#filterLocation").value = "all";
      renderMapView();
    });

    // Search input (real-time with auto-switch if in honeymoon/playlists and no results in current tab)
    let searchTimer = null;
    $("#searchInput").addEventListener("input", (e) => {
      const val = e.target.value;
      $("#btnSearchClear").classList.toggle("hidden", !val);
      clearTimeout(searchTimer);
      searchTimer = setTimeout(() => {
        uiState.searchQuery = val;
        uiState.allViewLimit = 60;
        if (val.trim() && uiState.currentView === "honeymoon") {
          // If searching for something not in honeymoon (e.g. 山形 ラーメン), automatically switch to All Videos view!
          const hmMatches = filterVideos(allVideos.filter((v) => v.honeymoon_season_id));
          if (hmMatches.length === 0) {
            switchView("all");
            return;
          }
        }
        renderCurrentView();
      }, 120);
    });

    $("#btnSearchClear").addEventListener("click", () => {
      $("#searchInput").value = "";
      uiState.searchQuery = "";
      $("#btnSearchClear").classList.add("hidden");
      renderCurrentView();
    });

    $("#chkSearchDesc").addEventListener("change", (e) => {
      uiState.searchDesc = e.target.checked;
      renderCurrentView();
    });

    if ($("#btnMobileFilterToggle")) {
      $("#btnMobileFilterToggle").addEventListener("click", () => {
        const panel = $("#searchRowFilters");
        const isExpanded = panel.classList.toggle("mobile-expanded");
        $("#btnMobileFilterToggle").textContent = isExpanded
          ? "⚙️ 絞り込みを閉じる ▲"
          : "⚙️ 絞り込み・並び替え ▼";
      });
    }

    // Channel segmented buttons
    $$("#channelFilterGroup .seg-btn").forEach((btn) => {
      btn.addEventListener("click", () => setChannelFilter(btn.dataset.channel));
    });

    // Select dropdowns
    $("#filterStatus").addEventListener("change", (e) => {
      uiState.status = e.target.value;
      updateHeaderStats();
      renderCurrentView();
    });

    $("#filterCategory").addEventListener("change", (e) => {
      uiState.category = e.target.value;
      if (uiState.category !== "all" && uiState.category !== "ハネムーン" && uiState.currentView === "honeymoon") {
        switchView("all");
      } else {
        renderCurrentView();
      }
    });

    $("#filterSeason").addEventListener("change", (e) => {
      uiState.season = e.target.value;
      if (uiState.season !== "all" && uiState.currentView !== "honeymoon") {
        switchView("honeymoon");
      } else {
        renderCurrentView();
      }
    });

    $("#filterLocation").addEventListener("change", (e) => {
      uiState.location = e.target.value;
      if (uiState.location.startsWith("pref:") || uiState.location.startsWith("region:")) {
        if (uiState.currentView === "honeymoon") switchView("all");
        else renderCurrentView();
      } else {
        renderCurrentView();
      }
    });

    $("#filterYear").addEventListener("change", (e) => {
      uiState.year = e.target.value;
      if (uiState.year !== "all" && Number(uiState.year) < 2023 && uiState.currentView === "honeymoon") {
        switchView("all");
      } else {
        renderCurrentView();
      }
    });

    $("#filterDuration").addEventListener("change", (e) => {
      uiState.duration = e.target.value;
      renderCurrentView();
    });

    $("#sortBy").addEventListener("change", (e) => {
      uiState.sortBy = e.target.value;
      renderCurrentView();
    });

    $("#chkExcludeShorts").addEventListener("change", (e) => {
      uiState.excludeShorts = e.target.checked;
      renderCurrentView();
    });

    $("#chkHmIncludeSub").addEventListener("change", (e) => {
      uiState.hmIncludeSub = e.target.checked;
      renderHoneymoonView();
    });

    $("#chkHmChronological").addEventListener("change", (e) => {
      uiState.hmChronological = e.target.checked;
      renderHoneymoonView();
    });

    // Layout switcher
    $$("#layoutSwitcher .layout-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        uiState.layout = btn.dataset.layout;
        $$("#layoutSwitcher .layout-btn").forEach((b) => b.classList.toggle("active", b.dataset.layout === uiState.layout));
        if (uiState.layout === "timeline" && uiState.currentView !== "all") {
          switchView("all");
        } else {
          renderCurrentView();
        }
      });
    });

    // Reset filters
    const resetAllFilters = () => {
      uiState.searchQuery = "";
      $("#searchInput").value = "";
      $("#btnSearchClear").classList.add("hidden");
      uiState.channel = "all";
      $$("#channelFilterGroup .seg-btn").forEach((b) => b.classList.toggle("active", b.dataset.channel === "all"));
      uiState.status = "all";
      $("#filterStatus").value = "all";
      uiState.category = "all";
      $("#filterCategory").value = "all";
      uiState.season = "all";
      $("#filterSeason").value = "all";
      uiState.location = "all";
      $("#filterLocation").value = "all";
      uiState.year = "all";
      $("#filterYear").value = "all";
      uiState.duration = "all";
      $("#filterDuration").value = "all";
      uiState.excludeShorts = false;
      $("#chkExcludeShorts").checked = false;
      uiState.allViewLimit = 60;
      updateHeaderStats();
      renderCurrentView();
    };

    $("#btnResetFilters").addEventListener("click", resetAllFilters);
    $("#brandReset").addEventListener("click", resetAllFilters);

    // Quick Header Stat Filters
    $("#quickFilterWatched").addEventListener("click", () => {
      uiState.status = uiState.status === "watched" ? "all" : "watched";
      $("#filterStatus").value = uiState.status;
      updateHeaderStats();
      if (uiState.status !== "all" && uiState.currentView !== "all") switchView("all");
      else renderCurrentView();
    });
    $("#quickFilterFav").addEventListener("click", () => {
      uiState.status = uiState.status === "favorite" ? "all" : "favorite";
      $("#filterStatus").value = uiState.status;
      updateHeaderStats();
      if (uiState.status !== "all" && uiState.currentView !== "all") switchView("all");
      else renderCurrentView();
    });
    $("#quickFilterLater").addEventListener("click", () => {
      uiState.status = uiState.status === "watch_later" ? "all" : "watch_later";
      $("#filterStatus").value = uiState.status;
      updateHeaderStats();
      if (uiState.status !== "all" && uiState.currentView !== "all") switchView("all");
      else renderCurrentView();
    });

    // Load more in All Videos view
    $("#btnLoadMore").addEventListener("click", () => {
      uiState.allViewLimit += 60;
      renderAllVideosView();
    });

    // Delegated clicks inside main container (cards, tags, state buttons, modal open)
    document.querySelector(".main-container").addEventListener("click", (e) => {
      const actionBtn = e.target.closest("[data-action]");
      if (actionBtn) {
        e.stopPropagation();
        toggleVideoState(actionBtn.dataset.vid, actionBtn.dataset.action);
        return;
      }

      const locTag = e.target.closest("[data-filter-loc]");
      if (locTag) {
        e.stopPropagation();
        const loc = locTag.dataset.filterLoc;
        uiState.location = uiState.location === loc ? "all" : loc;
        $("#filterLocation").value = uiState.location;
        if (loc.startsWith("pref:") && uiState.currentView === "honeymoon") {
          switchView("all");
        } else {
          renderCurrentView();
        }
        return;
      }

      const seasonTag = e.target.closest("[data-filter-season]");
      if (seasonTag) {
        e.stopPropagation();
        uiState.season = seasonTag.dataset.filterSeason;
        $("#filterSeason").value = uiState.season;
        switchView("honeymoon");
        return;
      }

      const catTag = e.target.closest("[data-filter-cat]");
      if (catTag) {
        e.stopPropagation();
        uiState.category = catTag.dataset.filterCat;
        $("#filterCategory").value = uiState.category;
        switchView("all");
        return;
      }

      const modalTrigger = e.target.closest("[data-open-modal]");
      if (modalTrigger) {
        openVideoModal(modalTrigger.dataset.openModal);
      }
    });

    // Modal controls
    $("#btnCloseVideoModal").addEventListener("click", closeVideoModal);
    $("#videoModal").addEventListener("click", (e) => {
      if (e.target.id === "videoModal") closeVideoModal();
    });

    $("#modalBtnWatched").addEventListener("click", () => {
      if (uiState.modalVideoId) toggleVideoState(uiState.modalVideoId, "watched");
    });
    $("#modalBtnFav").addEventListener("click", () => {
      if (uiState.modalVideoId) toggleVideoState(uiState.modalVideoId, "favorite");
    });
    $("#modalBtnLater").addEventListener("click", () => {
      if (uiState.modalVideoId) toggleVideoState(uiState.modalVideoId, "watch_later");
    });

    $("#btnSaveNote").addEventListener("click", () => {
      if (!uiState.modalVideoId) return;
      saveVideoNote(uiState.modalVideoId, $("#modalNoteInput").value);
      const btn = $("#btnSaveNote");
      btn.textContent = "✓ 保存しました";
      setTimeout(() => {
        btn.textContent = "メモ保存";
      }, 1400);
    });

    $("#modalBtnPrev").addEventListener("click", () => {
      const idx = uiState.modalContextList.indexOf(uiState.modalVideoId);
      if (idx > 0) openVideoModal(uiState.modalContextList[idx - 1]);
    });
    $("#modalBtnNext").addEventListener("click", () => {
      const idx = uiState.modalContextList.indexOf(uiState.modalVideoId);
      if (idx !== -1 && idx < uiState.modalContextList.length - 1) {
        openVideoModal(uiState.modalContextList[idx + 1]);
      }
    });

    // Keyboard shortcuts
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") {
        if (!$("#videoModal").classList.contains("hidden")) closeVideoModal();
        if (!$("#syncModal").classList.contains("hidden")) $("#syncModal").classList.add("hidden");
        if (!$("#backupModal").classList.contains("hidden")) $("#backupModal").classList.add("hidden");
      }
    });

    // Theme toggle
    const savedTheme = localStorage.getItem("tottabi_theme") || "dark";
    document.documentElement.setAttribute("data-theme", savedTheme);
    $("#btnThemeToggle").textContent = savedTheme === "dark" ? "🌙" : "☀️";
    $("#btnThemeToggle").addEventListener("click", () => {
      const cur = document.documentElement.getAttribute("data-theme") || "dark";
      const next = cur === "dark" ? "light" : "dark";
      document.documentElement.setAttribute("data-theme", next);
      localStorage.setItem("tottabi_theme", next);
      $("#btnThemeToggle").textContent = next === "dark" ? "🌙" : "☀️";
    });

    // Sync Modal & Polling
    $("#btnSyncOpen").addEventListener("click", () => $("#syncModal").classList.remove("hidden"));
    $("#btnCloseSyncModal").addEventListener("click", () => $("#syncModal").classList.add("hidden"));
    $("#syncModal").addEventListener("click", (e) => {
      if (e.target.id === "syncModal") $("#syncModal").classList.add("hidden");
    });

    const startSync = async (forceFull) => {
      if (isStandalone()) return;
      $("#syncModal").classList.add("hidden");
      $("#syncBanner").classList.remove("hidden");
      try {
        await fetch("/api/sync", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ force_full: forceFull }),
        });
        pollSyncStatus();
      } catch (err) {
        alert("同期の開始に失敗しました: " + err);
      }
    };

    if ($("#btnRunQuickSync")) {
      $("#btnRunQuickSync").addEventListener("click", () => startSync(false));
    }
    if ($("#btnRunFullSync")) {
      $("#btnRunFullSync").addEventListener("click", () => startSync(true));
    }

    // Backup / Export / Import Modal
    $("#btnBackupOpen").addEventListener("click", () => $("#backupModal").classList.remove("hidden"));
    $("#btnCloseBackupModal").addEventListener("click", () => $("#backupModal").classList.add("hidden"));
    $("#backupModal").addEventListener("click", (e) => {
      if (e.target.id === "backupModal") $("#backupModal").classList.add("hidden");
    });

    $("#btnExportState").addEventListener("click", () => {
      const dataStr = JSON.stringify(
        {
          favorites: Array.from(userState.favorites),
          watched: Array.from(userState.watched),
          watch_later: Array.from(userState.watch_later),
          notes: userState.notes,
          exported_at: new Date().toISOString(),
        },
        null,
        2
      );
      const blob = new Blob([dataStr], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `tottabi_userdata_${new Date().toISOString().slice(0, 10)}.json`;
      a.click();
      URL.revokeObjectURL(url);
    });

    $("#inputImportState").addEventListener("change", async (e) => {
      const file = e.target.files && e.target.files[0];
      if (!file) return;
      try {
        const text = await file.text();
        const parsed = JSON.parse(text);
        if (isStandalone()) {
          applyServerUserState(parsed);
          renderCurrentView();
          $("#backupModal").classList.add("hidden");
          alert("お気に入り・視聴済みデータを復元しました！");
          return;
        }
        const resp = await fetch("/api/user-state/import", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(parsed),
        });
        const resData = await resp.json();
        if (resData.ok) {
          applyServerUserState(resData.user_state);
          renderCurrentView();
          $("#backupModal").classList.add("hidden");
          alert("お気に入り・視聴済みデータを復元しました！");
        }
      } catch (err) {
        alert("JSONファイルの読み込みに失敗しました: " + err);
      }
    });
  }

  async function pollSyncStatus() {
    const timer = setInterval(async () => {
      try {
        const r = await fetch("/api/sync/status");
        const st = await r.json();
        $("#syncBannerMsg").textContent = st.message || "同期中...";
        $("#syncProgressFill").style.width = `${st.progress || 0}%`;
        if (!st.is_syncing) {
          clearInterval(timer);
          await loadDataset();
          setTimeout(() => {
            $("#syncBanner").classList.add("hidden");
          }, 2000);
        }
      } catch (_) {
        clearInterval(timer);
      }
    }, 800);
  }

  function hydrateVideo(v) {
    if (!v.thumbnail) v.thumbnail = `https://i.ytimg.com/vi/${v.id}/mqdefault.jpg`;
    if (!v.url) v.url = `https://www.youtube.com/watch?v=${v.id}`;
    if (!v.channel_name) v.channel_name = v.channel_key === "tottabi_biyori" ? "とったび日和" : "とったび";
    if (!v.publish_year && v.publish_date) v.publish_year = v.publish_date.slice(0, 4);
    if (!v.publish_month && v.publish_date) v.publish_month = v.publish_date.slice(0, 7);
    if (!v.prefectures) v.prefectures = [];
    if (!v.japan_regions) v.japan_regions = [];
    if (!v.overseas_countries) v.overseas_countries = [];
    if (!v.playlists) v.playlists = [];
    if (!v.playlist_titles) v.playlist_titles = v.playlists.map((p) => p.title);
    if (!v.description) v.description = v.excerpt || "";
    return v;
  }

  // -------------------------------------------------------------------------
  // Initial Data Load
  // -------------------------------------------------------------------------
  async function loadDataset() {
    let initialUserState = null;
    if (window.__TOTTABI_DATASET__) {
      dataset = window.__TOTTABI_DATASET__;
      initialUserState = window.__TOTTABI_USER_STATE__ || null;
    } else {
      const resp = await fetch("/api/dataset");
      const payload = await resp.json();
      dataset = payload.dataset;
      initialUserState = payload.user_state;
    }

    allVideos = (dataset.videos || []).map(hydrateVideo);
    videoMap = new Map(allVideos.map((v) => [v.id, v]));
    countryFlagMap = new Map((dataset.overseas_countries || []).map((c) => [c.name, c.flag]));

    applyServerUserState(initialUserState);
    populateFilterDropdowns();
    renderCurrentView();
  }

  document.addEventListener("DOMContentLoaded", () => {
    bindEvents();
    loadDataset();
  });
})();
