"""
Tracking pixel generator for email and content tracking.

This module provides:
- Generation of unique tracking pixels for email opens
- JavaScript tracking snippets for web content
- Pixel serving endpoint support
- Privacy-compliant tracking options
"""

import base64
import hashlib
import hmac
import logging
import os
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from urllib.parse import urlencode

logger = logging.getLogger(__name__)


class TrackingPixelGenerator:
    """
    Generator for tracking pixels and JavaScript snippets.

    This class creates tracking mechanisms for monitoring content performance
    across email, web, and embedded contexts.
    """

    # 1x1 transparent GIF
    TRANSPARENT_GIF = base64.b64decode(
        "R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"
    )

    def __init__(
        self,
        base_url: Optional[str] = None,
        secret_key: Optional[str] = None,
        token_expiry_hours: int = 720,  # 30 days default
    ):
        """
        Initialize the tracking pixel generator.

        Args:
            base_url: Base URL for tracking endpoints.
            secret_key: Secret key for signing tokens.
            token_expiry_hours: Hours until tracking tokens expire.
        """
        self._base_url = base_url or os.environ.get(
            "TRACKING_BASE_URL",
            os.environ.get("API_BASE_URL", "http://localhost:8000"),
        )
        self._secret_key = secret_key or os.environ.get(
            "TRACKING_SECRET_KEY",
            os.environ.get("WEBHOOK_SECRET", secrets.token_hex(32)),
        )
        self._token_expiry_hours = token_expiry_hours

    def _generate_token(
        self,
        content_id: str,
        event_type: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Generate a signed tracking token.

        Args:
            content_id: Content identifier.
            event_type: Type of event to track.
            metadata: Additional metadata to include.

        Returns:
            Signed token string.
        """
        import json

        timestamp = datetime.utcnow().isoformat()
        expiry = (datetime.utcnow() + timedelta(hours=self._token_expiry_hours)).isoformat()

        payload = {
            "cid": content_id,
            "evt": event_type,
            "ts": timestamp,
            "exp": expiry,
        }

        if metadata:
            payload["meta"] = metadata

        # Encode payload
        payload_json = json.dumps(payload, separators=(",", ":"))
        payload_b64 = base64.urlsafe_b64encode(payload_json.encode()).decode().rstrip("=")

        # Create signature
        signature = hmac.new(
            self._secret_key.encode(),
            payload_b64.encode(),
            hashlib.sha256,
        ).hexdigest()[:16]

        return f"{payload_b64}.{signature}"

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify and decode a tracking token.

        Args:
            token: Token to verify.

        Returns:
            Decoded payload if valid, None otherwise.
        """
        import json

        try:
            parts = token.rsplit(".", 1)
            if len(parts) != 2:
                return None

            payload_b64, signature = parts

            # Verify signature
            expected_sig = hmac.new(
                self._secret_key.encode(),
                payload_b64.encode(),
                hashlib.sha256,
            ).hexdigest()[:16]

            if not hmac.compare_digest(signature, expected_sig):
                logger.warning("Invalid tracking token signature")
                return None

            # Decode payload
            # Add padding back
            padding = 4 - len(payload_b64) % 4
            if padding != 4:
                payload_b64 += "=" * padding

            payload_json = base64.urlsafe_b64decode(payload_b64).decode()
            payload = json.loads(payload_json)

            # Check expiry
            expiry = datetime.fromisoformat(payload.get("exp", "2000-01-01"))
            if datetime.utcnow() > expiry:
                logger.debug("Tracking token expired")
                return None

            return payload

        except Exception as e:
            logger.error(f"Failed to verify token: {e}")
            return None

    # =========================================================================
    # Email Tracking
    # =========================================================================

    def generate_email_pixel(
        self,
        content_id: str,
        campaign_id: Optional[str] = None,
        recipient_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Generate a tracking pixel URL for email opens.

        Args:
            content_id: Content/email identifier.
            campaign_id: Optional campaign identifier.
            recipient_id: Optional recipient identifier (hashed for privacy).
            metadata: Additional tracking metadata.

        Returns:
            URL string for the tracking pixel.
        """
        meta = metadata or {}
        if campaign_id:
            meta["cmp"] = campaign_id
        if recipient_id:
            # Hash recipient ID for privacy
            meta["rid"] = hashlib.sha256(recipient_id.encode()).hexdigest()[:12]

        token = self._generate_token(content_id, "email_open", meta)

        params = {"t": token}
        return f"{self._base_url}/tracking/pixel.gif?{urlencode(params)}"

    def generate_email_pixel_html(
        self,
        content_id: str,
        campaign_id: Optional[str] = None,
        recipient_id: Optional[str] = None,
        alt_text: str = "",
    ) -> str:
        """
        Generate HTML img tag for email tracking pixel.

        Args:
            content_id: Content/email identifier.
            campaign_id: Optional campaign identifier.
            recipient_id: Optional recipient identifier.
            alt_text: Alt text for accessibility (optional).

        Returns:
            HTML string containing the tracking pixel img tag.
        """
        pixel_url = self.generate_email_pixel(content_id, campaign_id, recipient_id)

        return (
            f'<img src="{pixel_url}" width="1" height="1" '
            f'alt="{alt_text}" style="display:none;width:1px;height:1px;border:0;" />'
        )

    def generate_click_tracking_url(
        self,
        content_id: str,
        target_url: str,
        link_id: Optional[str] = None,
        campaign_id: Optional[str] = None,
    ) -> str:
        """
        Generate a click-tracking redirect URL.

        Args:
            content_id: Content identifier.
            target_url: Destination URL after tracking.
            link_id: Optional link identifier.
            campaign_id: Optional campaign identifier.

        Returns:
            URL string for click tracking redirect.
        """
        meta = {"url": target_url}
        if link_id:
            meta["lid"] = link_id
        if campaign_id:
            meta["cmp"] = campaign_id

        token = self._generate_token(content_id, "click", meta)

        params = {"t": token}
        return f"{self._base_url}/tracking/click?{urlencode(params)}"

    # =========================================================================
    # Web Tracking
    # =========================================================================

    def generate_tracking_script(
        self,
        content_id: str,
        options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Generate JavaScript tracking snippet for web content.

        Args:
            content_id: Content identifier.
            options: Tracking options (track_time, track_scroll, etc.).

        Returns:
            JavaScript code string.
        """
        opts = options or {}
        track_time = opts.get("track_time", True)
        track_scroll = opts.get("track_scroll", True)
        track_clicks = opts.get("track_clicks", False)
        sample_rate = opts.get("sample_rate", 1.0)

        token = self._generate_token(content_id, "pageview")

        script = f'''
<!-- Blog AI Performance Tracking -->
<script>
(function() {{
  var BLOG_AI_TRACKING = {{
    contentId: "{content_id}",
    token: "{token}",
    endpoint: "{self._base_url}/tracking/beacon",
    trackTime: {str(track_time).lower()},
    trackScroll: {str(track_scroll).lower()},
    trackClicks: {str(track_clicks).lower()},
    sampleRate: {sample_rate}
  }};

  // Only track based on sample rate
  if (Math.random() > BLOG_AI_TRACKING.sampleRate) return;

  var startTime = Date.now();
  var maxScroll = 0;
  var engaged = false;

  // Track page view
  function sendBeacon(eventType, data) {{
    var payload = {{
      t: BLOG_AI_TRACKING.token,
      e: eventType,
      d: data || {{}}
    }};

    if (navigator.sendBeacon) {{
      navigator.sendBeacon(
        BLOG_AI_TRACKING.endpoint,
        JSON.stringify(payload)
      );
    }} else {{
      var xhr = new XMLHttpRequest();
      xhr.open('POST', BLOG_AI_TRACKING.endpoint, true);
      xhr.setRequestHeader('Content-Type', 'application/json');
      xhr.send(JSON.stringify(payload));
    }}
  }}

  // Initial view
  sendBeacon('view');

  // Track scroll depth
  if (BLOG_AI_TRACKING.trackScroll) {{
    window.addEventListener('scroll', function() {{
      var scrollTop = window.pageYOffset || document.documentElement.scrollTop;
      var docHeight = document.documentElement.scrollHeight - window.innerHeight;
      var scrollPercent = docHeight > 0 ? (scrollTop / docHeight) : 0;

      if (scrollPercent > maxScroll) {{
        maxScroll = scrollPercent;
        if (!engaged && maxScroll > 0.25) {{
          engaged = true;
          sendBeacon('engaged');
        }}
      }}
    }}, {{ passive: true }});
  }}

  // Track time on page
  if (BLOG_AI_TRACKING.trackTime) {{
    window.addEventListener('beforeunload', function() {{
      var timeOnPage = Math.round((Date.now() - startTime) / 1000);
      var isBounce = timeOnPage < 10 && maxScroll < 0.1;

      sendBeacon('leave', {{
        time: timeOnPage,
        scroll: Math.round(maxScroll * 100),
        bounce: isBounce
      }});
    }});

    // Also send periodic pings for long sessions
    setInterval(function() {{
      var timeOnPage = Math.round((Date.now() - startTime) / 1000);
      if (timeOnPage > 0 && timeOnPage % 60 === 0) {{
        sendBeacon('heartbeat', {{
          time: timeOnPage,
          scroll: Math.round(maxScroll * 100)
        }});
      }}
    }}, 60000);
  }}

  // Track outbound clicks
  if (BLOG_AI_TRACKING.trackClicks) {{
    document.addEventListener('click', function(e) {{
      var link = e.target.closest('a');
      if (link && link.hostname !== window.location.hostname) {{
        sendBeacon('outbound_click', {{
          url: link.href,
          text: link.innerText.substring(0, 50)
        }});
      }}
    }});
  }}
}})();
</script>
'''
        return script.strip()

    def generate_minimal_tracking_script(self, content_id: str) -> str:
        """
        Generate a minimal tracking script (view only).

        Args:
            content_id: Content identifier.

        Returns:
            Minimal JavaScript code string.
        """
        token = self._generate_token(content_id, "pageview")

        return f'''
<script>
(function(){{
  var img=new Image();
  img.src="{self._base_url}/tracking/pixel.gif?t={token}";
}})();
</script>
'''

    # =========================================================================
    # Share Tracking
    # =========================================================================

    def generate_share_tracking_url(
        self,
        content_id: str,
        platform: str,
        share_url: str,
        share_text: Optional[str] = None,
    ) -> str:
        """
        Generate a share tracking URL.

        Args:
            content_id: Content identifier.
            platform: Social platform (twitter, facebook, linkedin, etc.).
            share_url: URL to share.
            share_text: Optional share text.

        Returns:
            Tracking URL that redirects to the platform share dialog.
        """
        meta = {
            "platform": platform,
            "share_url": share_url,
        }
        if share_text:
            meta["text"] = share_text[:100]  # Limit text length

        token = self._generate_token(content_id, "share", meta)

        # Build platform-specific share URL
        share_dialogs = {
            "twitter": f"https://twitter.com/intent/tweet?url={share_url}&text={share_text or ''}",
            "facebook": f"https://www.facebook.com/sharer/sharer.php?u={share_url}",
            "linkedin": f"https://www.linkedin.com/sharing/share-offsite/?url={share_url}",
            "email": f"mailto:?subject={share_text or ''}&body={share_url}",
        }

        target = share_dialogs.get(platform, share_url)

        params = {
            "t": token,
            "target": target,
        }

        return f"{self._base_url}/tracking/share?{urlencode(params)}"

    # =========================================================================
    # Utility Methods
    # =========================================================================

    @staticmethod
    def get_transparent_gif() -> bytes:
        """Get the 1x1 transparent GIF bytes."""
        return TrackingPixelGenerator.TRANSPARENT_GIF

    def generate_noscript_tracking(self, content_id: str) -> str:
        """
        Generate noscript fallback tracking.

        Args:
            content_id: Content identifier.

        Returns:
            HTML noscript tag with tracking pixel.
        """
        pixel_url = self.generate_email_pixel(content_id)
        return f'''
<noscript>
  <img src="{pixel_url}" width="1" height="1" alt="" style="display:none" />
</noscript>
'''

    def generate_amp_tracking(self, content_id: str) -> str:
        """
        Generate AMP-compatible tracking pixel.

        Args:
            content_id: Content identifier.

        Returns:
            AMP analytics component HTML.
        """
        token = self._generate_token(content_id, "amp_pageview")

        return f'''
<amp-pixel src="{self._base_url}/tracking/pixel.gif?t={token}&amp;RANDOM"></amp-pixel>
<amp-analytics type="blogai">
  <script type="application/json">
  {{
    "requests": {{
      "pageview": "{self._base_url}/tracking/beacon?t={token}&e=pageview",
      "event": "{self._base_url}/tracking/beacon?t={token}&e=${{eventType}}"
    }},
    "triggers": {{
      "trackPageview": {{
        "on": "visible",
        "request": "pageview"
      }},
      "trackScroll": {{
        "on": "scroll",
        "scrollSpec": {{
          "verticalBoundaries": [25, 50, 75, 90]
        }},
        "request": "event",
        "vars": {{
          "eventType": "scroll"
        }}
      }}
    }}
  }}
  </script>
</amp-analytics>
'''
