"use strict";(self.webpackChunk_N_E=self.webpackChunk_N_E||[]).push([[814],{1231:function(e,t,n){let r;n.d(t,{Z:function(){return a}});var o={randomUUID:"undefined"!=typeof crypto&&crypto.randomUUID&&crypto.randomUUID.bind(crypto)};let l=new Uint8Array(16),u=[];for(let e=0;e<256;++e)u.push((e+256).toString(16).slice(1));var a=function(e,t,n){if(o.randomUUID&&!t&&!e)return o.randomUUID();let a=(e=e||{}).random||(e.rng||function(){if(!r&&!(r="undefined"!=typeof crypto&&crypto.getRandomValues&&crypto.getRandomValues.bind(crypto)))throw Error("crypto.getRandomValues() not supported. See https://github.com/uuidjs/uuid#getrandomvalues-not-supported");return r(l)})();if(a[6]=15&a[6]|64,a[8]=63&a[8]|128,t){n=n||0;for(let e=0;e<16;++e)t[n+e]=a[e];return t}return function(e){let t=arguments.length>1&&void 0!==arguments[1]?arguments[1]:0;return u[e[t+0]]+u[e[t+1]]+u[e[t+2]]+u[e[t+3]]+"-"+u[e[t+4]]+u[e[t+5]]+"-"+u[e[t+6]]+u[e[t+7]]+"-"+u[e[t+8]]+u[e[t+9]]+"-"+u[e[t+10]]+u[e[t+11]]+u[e[t+12]]+u[e[t+13]]+u[e[t+14]]+u[e[t+15]]}(a)}},7409:function(e,t,n){n.d(t,{R:function(){return o}});var r,o=((r=o||{}).Space=" ",r.Enter="Enter",r.Escape="Escape",r.Backspace="Backspace",r.Delete="Delete",r.ArrowLeft="ArrowLeft",r.ArrowUp="ArrowUp",r.ArrowRight="ArrowRight",r.ArrowDown="ArrowDown",r.Home="Home",r.End="End",r.PageUp="PageUp",r.PageDown="PageDown",r.Tab="Tab",r)},7607:function(e,t,n){n.d(t,{J:function(){return ed}});var r,o,l,u,a,i,s,c,d,f=n(4090),p=n(9542),v=n(641),m=n(9790),h=n(1210),g=n(1879);function y(e){return g.O.isServer?null:e instanceof Node?e.ownerDocument:null!=e&&e.hasOwnProperty("current")&&e.current instanceof Node?e.current.ownerDocument:document}function b(){for(var e=arguments.length,t=Array(e),n=0;n<e;n++)t[n]=arguments[n];return(0,f.useMemo)(()=>y(...t),[...t])}var E=n(2144),P=n(6601);let S=(0,f.createContext)(!1);var w=n(7306);let T=f.Fragment,N=f.Fragment,O=(0,f.createContext)(null),A=(0,f.createContext)(null);Object.assign((0,w.yV)(function(e,t){let n,r,o=(0,f.useRef)(null),l=(0,P.T)((0,P.h)(e=>{o.current=e}),t),u=b(o),a=function(e){let t=(0,f.useContext)(S),n=(0,f.useContext)(O),r=b(e),[o,l]=(0,f.useState)(()=>{if(!t&&null!==n||g.O.isServer)return null;let e=null==r?void 0:r.getElementById("headlessui-portal-root");if(e)return e;if(null===r)return null;let o=r.createElement("div");return o.setAttribute("id","headlessui-portal-root"),r.body.appendChild(o)});return(0,f.useEffect)(()=>{null!==o&&(null!=r&&r.body.contains(o)||null==r||r.body.appendChild(o))},[o,r]),(0,f.useEffect)(()=>{t||null!==n&&l(n.current)},[n,l,t]),o}(o),[i]=(0,f.useState)(()=>{var e;return g.O.isServer?null:null!=(e=null==u?void 0:u.createElement("div"))?e:null}),s=(0,f.useContext)(A),c=(0,E.H)();return(0,m.e)(()=>{!a||!i||a.contains(i)||(i.setAttribute("data-headlessui-portal",""),a.appendChild(i))},[a,i]),(0,m.e)(()=>{if(i&&s)return s.register(i)},[s,i]),n=(0,v.z)(()=>{var e;a&&i&&(i instanceof Node&&a.contains(i)&&a.removeChild(i),a.childNodes.length<=0&&(null==(e=a.parentElement)||e.removeChild(a)))}),r=(0,f.useRef)(!1),(0,f.useEffect)(()=>(r.current=!1,()=>{r.current=!0,(0,h.Y)(()=>{r.current&&n()})}),[n]),c&&a&&i?(0,p.createPortal)((0,w.sY)({ourProps:{ref:l},theirProps:e,defaultTag:T,name:"Portal"}),i):null}),{Group:(0,w.yV)(function(e,t){let{target:n,...r}=e,o={ref:(0,P.T)(t)};return f.createElement(O.Provider,{value:n},(0,w.sY)({ourProps:o,theirProps:r,defaultTag:N,name:"Popover.Group"}))})});var C=n(5235),x=n(1313),M=n(2640);let I=["[contentEditable=true]","[tabindex]","a[href]","area[href]","button:not([disabled])","iframe","input:not([disabled])","select:not([disabled])","textarea:not([disabled])"].map(e=>"".concat(e,":not([tabindex='-1'])")).join(",");var k=((r=k||{})[r.First=1]="First",r[r.Previous=2]="Previous",r[r.Next=4]="Next",r[r.Last=8]="Last",r[r.WrapAround=16]="WrapAround",r[r.NoScroll=32]="NoScroll",r),F=((o=F||{})[o.Error=0]="Error",o[o.Overflow=1]="Overflow",o[o.Success=2]="Success",o[o.Underflow=3]="Underflow",o),R=((l=R||{})[l.Previous=-1]="Previous",l[l.Next=1]="Next",l);function L(){let e=arguments.length>0&&void 0!==arguments[0]?arguments[0]:document.body;return null==e?[]:Array.from(e.querySelectorAll(I)).sort((e,t)=>Math.sign((e.tabIndex||Number.MAX_SAFE_INTEGER)-(t.tabIndex||Number.MAX_SAFE_INTEGER)))}var D=((u=D||{})[u.Strict=0]="Strict",u[u.Loose=1]="Loose",u);function j(e){var t;let n=arguments.length>1&&void 0!==arguments[1]?arguments[1]:0;return e!==(null==(t=y(e))?void 0:t.body)&&(0,M.E)(n,{0:()=>e.matches(I),1(){let t=e;for(;null!==t;){if(t.matches(I))return!0;t=t.parentElement}return!1}})}var H=((a=H||{})[a.Keyboard=0]="Keyboard",a[a.Mouse=1]="Mouse",a);function z(e,t){var n,r,o;let{sorted:l=!0,relativeTo:u=null,skipElements:a=[]}=arguments.length>2&&void 0!==arguments[2]?arguments[2]:{},i=Array.isArray(e)?e.length>0?e[0].ownerDocument:document:e.ownerDocument,s=Array.isArray(e)?l?function(e){let t=arguments.length>1&&void 0!==arguments[1]?arguments[1]:e=>e;return e.slice().sort((e,n)=>{let r=t(e),o=t(n);if(null===r||null===o)return 0;let l=r.compareDocumentPosition(o);return l&Node.DOCUMENT_POSITION_FOLLOWING?-1:l&Node.DOCUMENT_POSITION_PRECEDING?1:0})}(e):e:L(e);a.length>0&&s.length>1&&(s=s.filter(e=>!a.includes(e))),u=null!=u?u:i.activeElement;let c=(()=>{if(5&t)return 1;if(10&t)return -1;throw Error("Missing Focus.First, Focus.Previous, Focus.Next or Focus.Last")})(),d=(()=>{if(1&t)return 0;if(2&t)return Math.max(0,s.indexOf(u))-1;if(4&t)return Math.max(0,s.indexOf(u))+1;if(8&t)return s.length-1;throw Error("Missing Focus.First, Focus.Previous, Focus.Next or Focus.Last")})(),f=32&t?{preventScroll:!0}:{},p=0,v=s.length,m;do{if(p>=v||p+v<=0)return 0;let e=d+p;if(16&t)e=(e+v)%v;else{if(e<0)return 3;if(e>=v)return 1}null==(m=s[e])||m.focus(f),p+=c}while(m!==i.activeElement);return 6&t&&null!=(o=null==(r=null==(n=m)?void 0:n.matches)?void 0:r.call(n,"textarea,input"))&&o&&m.select(),2}function _(e,t,n){let r=(0,C.E)(t);(0,f.useEffect)(()=>{function t(e){r.current(e)}return document.addEventListener(e,t,n),()=>document.removeEventListener(e,t,n)},[e,n])}function B(e,t,n){let r=(0,C.E)(t);(0,f.useEffect)(()=>{function t(e){r.current(e)}return window.addEventListener(e,t,n),()=>window.removeEventListener(e,t,n)},[e,n])}"undefined"!=typeof document&&(document.addEventListener("keydown",e=>{e.metaKey||e.altKey||e.ctrlKey||(document.documentElement.dataset.headlessuiFocusVisible="")},!0),document.addEventListener("click",e=>{1===e.detail?delete document.documentElement.dataset.headlessuiFocusVisible:0===e.detail&&(document.documentElement.dataset.headlessuiFocusVisible="")},!0));var U=n(1454),Y=n(7700),V=((i=V||{})[i.Forwards=0]="Forwards",i[i.Backwards=1]="Backwards",i);function G(){let e=(0,f.useRef)(0);return B("keydown",t=>{"Tab"===t.key&&(e.current=t.shiftKey?1:0)},!0),e}let K=(0,f.createContext)(null);K.displayName="OpenClosedContext";var q=((s=q||{})[s.Open=1]="Open",s[s.Closed=2]="Closed",s[s.Closing=4]="Closing",s[s.Opening=8]="Opening",s);function W(){return(0,f.useContext)(K)}function X(e){let{value:t,children:n}=e;return f.createElement(K.Provider,{value:t},n)}var J=n(4152),Z=n(7409),Q=((c=Q||{})[c.Open=0]="Open",c[c.Closed=1]="Closed",c),$=((d=$||{})[d.TogglePopover=0]="TogglePopover",d[d.ClosePopover=1]="ClosePopover",d[d.SetButton=2]="SetButton",d[d.SetButtonId=3]="SetButtonId",d[d.SetPanel=4]="SetPanel",d[d.SetPanelId=5]="SetPanelId",d);let ee={0:e=>{let t={...e,popoverState:(0,M.E)(e.popoverState,{0:1,1:0})};return 0===t.popoverState&&(t.__demoMode=!1),t},1:e=>1===e.popoverState?e:{...e,popoverState:1},2:(e,t)=>e.button===t.button?e:{...e,button:t.button},3:(e,t)=>e.buttonId===t.buttonId?e:{...e,buttonId:t.buttonId},4:(e,t)=>e.panel===t.panel?e:{...e,panel:t.panel},5:(e,t)=>e.panelId===t.panelId?e:{...e,panelId:t.panelId}},et=(0,f.createContext)(null);function en(e){let t=(0,f.useContext)(et);if(null===t){let t=Error("<".concat(e," /> is missing a parent <Popover /> component."));throw Error.captureStackTrace&&Error.captureStackTrace(t,en),t}return t}et.displayName="PopoverContext";let er=(0,f.createContext)(null);function eo(e){let t=(0,f.useContext)(er);if(null===t){let t=Error("<".concat(e," /> is missing a parent <Popover /> component."));throw Error.captureStackTrace&&Error.captureStackTrace(t,eo),t}return t}er.displayName="PopoverAPIContext";let el=(0,f.createContext)(null);function eu(){return(0,f.useContext)(el)}el.displayName="PopoverGroupContext";let ea=(0,f.createContext)(null);function ei(e,t){return(0,M.E)(t.type,ee,e,t)}ea.displayName="PopoverPanelContext";let es=w.AN.RenderStrategy|w.AN.Static,ec=w.AN.RenderStrategy|w.AN.Static,ed=Object.assign((0,w.yV)(function(e,t){var n,r,o;let l,u,a,i,s,c;let{__demoMode:d=!1,...p}=e,m=(0,f.useRef)(null),h=(0,P.T)(t,(0,P.h)(e=>{m.current=e})),g=(0,f.useRef)([]),y=(0,f.useReducer)(ei,{__demoMode:d,popoverState:d?0:1,buttons:g,button:null,buttonId:null,panel:null,panelId:null,beforePanelSentinel:(0,f.createRef)(),afterPanelSentinel:(0,f.createRef)()}),[{popoverState:E,button:S,buttonId:T,panel:N,panelId:O,beforePanelSentinel:x,afterPanelSentinel:I},k]=y,F=b(null!=(n=m.current)?n:S),R=(0,f.useMemo)(()=>{if(!S||!N)return!1;for(let e of document.querySelectorAll("body > *"))if(Number(null==e?void 0:e.contains(S))^Number(null==e?void 0:e.contains(N)))return!0;let e=L(),t=e.indexOf(S),n=(t+e.length-1)%e.length,r=(t+1)%e.length,o=e[n],l=e[r];return!N.contains(o)&&!N.contains(l)},[S,N]),H=(0,C.E)(T),z=(0,C.E)(O),U=(0,f.useMemo)(()=>({buttonId:H,panelId:z,close:()=>k({type:1})}),[H,z,k]),V=eu(),G=null==V?void 0:V.registerPopover,K=(0,v.z)(()=>{var e;return null!=(e=null==V?void 0:V.isFocusWithinPopoverGroup())?e:(null==F?void 0:F.activeElement)&&((null==S?void 0:S.contains(F.activeElement))||(null==N?void 0:N.contains(F.activeElement)))});(0,f.useEffect)(()=>null==G?void 0:G(U),[G,U]);let[W,J]=(l=(0,f.useContext)(A),u=(0,f.useRef)([]),a=(0,v.z)(e=>(u.current.push(e),l&&l.register(e),()=>i(e))),i=(0,v.z)(e=>{let t=u.current.indexOf(e);-1!==t&&u.current.splice(t,1),l&&l.unregister(e)}),s=(0,f.useMemo)(()=>({register:a,unregister:i,portals:u}),[a,i,u]),[u,(0,f.useMemo)(()=>function(e){let{children:t}=e;return f.createElement(A.Provider,{value:s},t)},[s])]),Z=function(){var e;let{defaultContainers:t=[],portals:n,mainTreeNodeRef:r}=arguments.length>0&&void 0!==arguments[0]?arguments[0]:{},o=(0,f.useRef)(null!=(e=null==r?void 0:r.current)?e:null),l=b(o),u=(0,v.z)(()=>{var e,r,u;let a=[];for(let e of t)null!==e&&(e instanceof HTMLElement?a.push(e):"current"in e&&e.current instanceof HTMLElement&&a.push(e.current));if(null!=n&&n.current)for(let e of n.current)a.push(e);for(let t of null!=(e=null==l?void 0:l.querySelectorAll("html > *, body > *"))?e:[])t!==document.body&&t!==document.head&&t instanceof HTMLElement&&"headlessui-portal-root"!==t.id&&(t.contains(o.current)||t.contains(null==(u=null==(r=o.current)?void 0:r.getRootNode())?void 0:u.host)||a.some(e=>t.contains(e))||a.push(t));return a});return{resolveContainers:u,contains:(0,v.z)(e=>u().some(t=>t.contains(e))),mainTreeNodeRef:o,MainTreeNode:(0,f.useMemo)(()=>function(){return null!=r?null:f.createElement(Y._,{features:Y.A.Hidden,ref:o})},[o,r])}}({mainTreeNodeRef:null==V?void 0:V.mainTreeNodeRef,portals:W,defaultContainers:[S,N]});r=null==F?void 0:F.defaultView,o="focus",c=(0,C.E)(e=>{var t,n,r,o;e.target!==window&&e.target instanceof HTMLElement&&0===E&&(K()||S&&N&&(Z.contains(e.target)||null!=(n=null==(t=x.current)?void 0:t.contains)&&n.call(t,e.target)||null!=(o=null==(r=I.current)?void 0:r.contains)&&o.call(r,e.target)||k({type:1})))}),(0,f.useEffect)(()=>{function e(e){c.current(e)}return(r=null!=r?r:window).addEventListener(o,e,!0),()=>r.removeEventListener(o,e,!0)},[r,o,!0]),function(e,t){let n=!(arguments.length>2)||void 0===arguments[2]||arguments[2],r=(0,f.useRef)(!1);function o(n,o){if(!r.current||n.defaultPrevented)return;let l=o(n);if(null!==l&&l.getRootNode().contains(l)&&l.isConnected){for(let t of function e(t){return"function"==typeof t?e(t()):Array.isArray(t)||t instanceof Set?t:[t]}(e)){if(null===t)continue;let e=t instanceof HTMLElement?t:t.current;if(null!=e&&e.contains(l)||n.composed&&n.composedPath().includes(e))return}return j(l,D.Loose)||-1===l.tabIndex||n.preventDefault(),t(n,l)}}(0,f.useEffect)(()=>{requestAnimationFrame(()=>{r.current=n})},[n]);let l=(0,f.useRef)(null);_("pointerdown",e=>{var t,n;r.current&&(l.current=(null==(n=null==(t=e.composedPath)?void 0:t.call(e))?void 0:n[0])||e.target)},!0),_("mousedown",e=>{var t,n;r.current&&(l.current=(null==(n=null==(t=e.composedPath)?void 0:t.call(e))?void 0:n[0])||e.target)},!0),_("click",e=>{/iPhone/gi.test(window.navigator.platform)||/Mac/gi.test(window.navigator.platform)&&window.navigator.maxTouchPoints>0||/Android/gi.test(window.navigator.userAgent)||l.current&&(o(e,()=>l.current),l.current=null)},!0),_("touchend",e=>o(e,()=>e.target instanceof HTMLElement?e.target:null),!0),B("blur",e=>o(e,()=>window.document.activeElement instanceof HTMLIFrameElement?window.document.activeElement:null),!0)}(Z.resolveContainers,(e,t)=>{k({type:1}),j(t,D.Loose)||(e.preventDefault(),null==S||S.focus())},0===E);let Q=(0,v.z)(e=>{k({type:1});let t=e?e instanceof HTMLElement?e:"current"in e&&e.current instanceof HTMLElement?e.current:S:S;null==t||t.focus()}),$=(0,f.useMemo)(()=>({close:Q,isPortalled:R}),[Q,R]),ee=(0,f.useMemo)(()=>({open:0===E,close:Q}),[E,Q]);return f.createElement(ea.Provider,{value:null},f.createElement(et.Provider,{value:y},f.createElement(er.Provider,{value:$},f.createElement(X,{value:(0,M.E)(E,{0:q.Open,1:q.Closed})},f.createElement(J,null,(0,w.sY)({ourProps:{ref:h},theirProps:p,slot:ee,defaultTag:"div",name:"Popover"}),f.createElement(Z.MainTreeNode,null))))))}),{Button:(0,w.yV)(function(e,t){let n=(0,x.M)(),{id:r="headlessui-popover-button-".concat(n),...o}=e,[l,u]=en("Popover.Button"),{isPortalled:a}=eo("Popover.Button"),i=(0,f.useRef)(null),s="headlessui-focus-sentinel-".concat((0,x.M)()),c=eu(),d=null==c?void 0:c.closeOthers,p=null!==(0,f.useContext)(ea);(0,f.useEffect)(()=>{if(!p)return u({type:3,buttonId:r}),()=>{u({type:3,buttonId:null})}},[p,r,u]);let[m]=(0,f.useState)(()=>Symbol()),h=(0,P.T)(i,t,p?null:e=>{if(e)l.buttons.current.push(m);else{let e=l.buttons.current.indexOf(m);-1!==e&&l.buttons.current.splice(e,1)}l.buttons.current.length>1&&console.warn("You are already using a <Popover.Button /> but only 1 <Popover.Button /> is supported."),e&&u({type:2,button:e})}),g=(0,P.T)(i,t),y=b(i),E=(0,v.z)(e=>{var t,n,r;if(p){if(1===l.popoverState)return;switch(e.key){case Z.R.Space:case Z.R.Enter:e.preventDefault(),null==(n=(t=e.target).click)||n.call(t),u({type:1}),null==(r=l.button)||r.focus()}}else switch(e.key){case Z.R.Space:case Z.R.Enter:e.preventDefault(),e.stopPropagation(),1===l.popoverState&&(null==d||d(l.buttonId)),u({type:0});break;case Z.R.Escape:if(0!==l.popoverState)return null==d?void 0:d(l.buttonId);if(!i.current||null!=y&&y.activeElement&&!i.current.contains(y.activeElement))return;e.preventDefault(),e.stopPropagation(),u({type:1})}}),S=(0,v.z)(e=>{p||e.key===Z.R.Space&&e.preventDefault()}),T=(0,v.z)(t=>{var n,r;(0,J.P)(t.currentTarget)||e.disabled||(p?(u({type:1}),null==(n=l.button)||n.focus()):(t.preventDefault(),t.stopPropagation(),1===l.popoverState&&(null==d||d(l.buttonId)),u({type:0}),null==(r=l.button)||r.focus()))}),N=(0,v.z)(e=>{e.preventDefault(),e.stopPropagation()}),O=0===l.popoverState,A=(0,f.useMemo)(()=>({open:O}),[O]),C=(0,U.f)(e,i),I=p?{ref:g,type:C,onKeyDown:E,onClick:T}:{ref:h,id:l.buttonId,type:C,"aria-expanded":0===l.popoverState,"aria-controls":l.panel?l.panelId:void 0,onKeyDown:E,onKeyUp:S,onClick:T,onMouseDown:N},R=G(),D=(0,v.z)(()=>{let e=l.panel;e&&(0,M.E)(R.current,{[V.Forwards]:()=>z(e,k.First),[V.Backwards]:()=>z(e,k.Last)})===F.Error&&z(L().filter(e=>"true"!==e.dataset.headlessuiFocusGuard),(0,M.E)(R.current,{[V.Forwards]:k.Next,[V.Backwards]:k.Previous}),{relativeTo:l.button})});return f.createElement(f.Fragment,null,(0,w.sY)({ourProps:I,theirProps:o,slot:A,defaultTag:"button",name:"Popover.Button"}),O&&!p&&a&&f.createElement(Y._,{id:s,features:Y.A.Focusable,"data-headlessui-focus-guard":!0,as:"button",type:"button",onFocus:D}))}),Overlay:(0,w.yV)(function(e,t){let n=(0,x.M)(),{id:r="headlessui-popover-overlay-".concat(n),...o}=e,[{popoverState:l},u]=en("Popover.Overlay"),a=(0,P.T)(t),i=W(),s=null!==i?(i&q.Open)===q.Open:0===l,c=(0,v.z)(e=>{if((0,J.P)(e.currentTarget))return e.preventDefault();u({type:1})}),d=(0,f.useMemo)(()=>({open:0===l}),[l]);return(0,w.sY)({ourProps:{ref:a,id:r,"aria-hidden":!0,onClick:c},theirProps:o,slot:d,defaultTag:"div",features:es,visible:s,name:"Popover.Overlay"})}),Panel:(0,w.yV)(function(e,t){let n=(0,x.M)(),{id:r="headlessui-popover-panel-".concat(n),focus:o=!1,...l}=e,[u,a]=en("Popover.Panel"),{close:i,isPortalled:s}=eo("Popover.Panel"),c="headlessui-focus-sentinel-before-".concat((0,x.M)()),d="headlessui-focus-sentinel-after-".concat((0,x.M)()),p=(0,f.useRef)(null),h=(0,P.T)(p,t,e=>{a({type:4,panel:e})}),g=b(p),y=(0,w.Y2)();(0,m.e)(()=>(a({type:5,panelId:r}),()=>{a({type:5,panelId:null})}),[r,a]);let E=W(),S=null!==E?(E&q.Open)===q.Open:0===u.popoverState,T=(0,v.z)(e=>{var t;if(e.key===Z.R.Escape){if(0!==u.popoverState||!p.current||null!=g&&g.activeElement&&!p.current.contains(g.activeElement))return;e.preventDefault(),e.stopPropagation(),a({type:1}),null==(t=u.button)||t.focus()}});(0,f.useEffect)(()=>{var t;e.static||1===u.popoverState&&(null==(t=e.unmount)||t)&&a({type:4,panel:null})},[u.popoverState,e.unmount,e.static,a]),(0,f.useEffect)(()=>{if(u.__demoMode||!o||0!==u.popoverState||!p.current)return;let e=null==g?void 0:g.activeElement;p.current.contains(e)||z(p.current,k.First)},[u.__demoMode,o,p,u.popoverState]);let N=(0,f.useMemo)(()=>({open:0===u.popoverState,close:i}),[u,i]),O={ref:h,id:r,onKeyDown:T,onBlur:o&&0===u.popoverState?e=>{var t,n,r,o,l;let i=e.relatedTarget;i&&p.current&&(null!=(t=p.current)&&t.contains(i)||(a({type:1}),(null!=(r=null==(n=u.beforePanelSentinel.current)?void 0:n.contains)&&r.call(n,i)||null!=(l=null==(o=u.afterPanelSentinel.current)?void 0:o.contains)&&l.call(o,i))&&i.focus({preventScroll:!0})))}:void 0,tabIndex:-1},A=G(),C=(0,v.z)(()=>{let e=p.current;e&&(0,M.E)(A.current,{[V.Forwards]:()=>{var t;z(e,k.First)===F.Error&&(null==(t=u.afterPanelSentinel.current)||t.focus())},[V.Backwards]:()=>{var e;null==(e=u.button)||e.focus({preventScroll:!0})}})}),I=(0,v.z)(()=>{let e=p.current;e&&(0,M.E)(A.current,{[V.Forwards]:()=>{var e;if(!u.button)return;let t=L(),n=t.indexOf(u.button),r=t.slice(0,n+1),o=[...t.slice(n+1),...r];for(let t of o.slice())if("true"===t.dataset.headlessuiFocusGuard||null!=(e=u.panel)&&e.contains(t)){let e=o.indexOf(t);-1!==e&&o.splice(e,1)}z(o,k.First,{sorted:!1})},[V.Backwards]:()=>{var t;z(e,k.Previous)===F.Error&&(null==(t=u.button)||t.focus())}})});return f.createElement(ea.Provider,{value:r},S&&s&&f.createElement(Y._,{id:c,ref:u.beforePanelSentinel,features:Y.A.Focusable,"data-headlessui-focus-guard":!0,as:"button",type:"button",onFocus:C}),(0,w.sY)({mergeRefs:y,ourProps:O,theirProps:l,slot:N,defaultTag:"div",features:ec,visible:S,name:"Popover.Panel"}),S&&s&&f.createElement(Y._,{id:d,ref:u.afterPanelSentinel,features:Y.A.Focusable,"data-headlessui-focus-guard":!0,as:"button",type:"button",onFocus:I}))}),Group:(0,w.yV)(function(e,t){let n;let r=(0,f.useRef)(null),o=(0,P.T)(r,t),[l,u]=(0,f.useState)([]),a={mainTreeNodeRef:n=(0,f.useRef)(null),MainTreeNode:(0,f.useMemo)(()=>function(){return f.createElement(Y._,{features:Y.A.Hidden,ref:n})},[n])},i=(0,v.z)(e=>{u(t=>{let n=t.indexOf(e);if(-1!==n){let e=t.slice();return e.splice(n,1),e}return t})}),s=(0,v.z)(e=>(u(t=>[...t,e]),()=>i(e))),c=(0,v.z)(()=>{var e;let t=y(r);if(!t)return!1;let n=t.activeElement;return!!(null!=(e=r.current)&&e.contains(n))||l.some(e=>{var r,o;return(null==(r=t.getElementById(e.buttonId.current))?void 0:r.contains(n))||(null==(o=t.getElementById(e.panelId.current))?void 0:o.contains(n))})}),d=(0,v.z)(e=>{for(let t of l)t.buttonId.current!==e&&t.close()}),p=(0,f.useMemo)(()=>({registerPopover:s,unregisterPopover:i,isFocusWithinPopoverGroup:c,closeOthers:d,mainTreeNodeRef:a.mainTreeNodeRef}),[s,i,c,d,a.mainTreeNodeRef]),m=(0,f.useMemo)(()=>({}),[]);return f.createElement(el.Provider,{value:p},(0,w.sY)({ourProps:{ref:o},theirProps:e,slot:m,defaultTag:"div",name:"Popover.Group"}),f.createElement(a.MainTreeNode,null))})})},5620:function(e,t,n){n.d(t,{r:function(){return E}});var r=n(4090),o=n(641),l=n(1210),u=n(1313),a=n(1454),i=n(6601),s=n(7700),c=n(4152),d=n(7306),f=n(9790);let p=(0,r.createContext)(null),v=Object.assign((0,d.yV)(function(e,t){let n=(0,u.M)(),{id:o="headlessui-description-".concat(n),...l}=e,a=function e(){let t=(0,r.useContext)(p);if(null===t){let t=Error("You used a <Description /> component, but it is not inside a relevant parent.");throw Error.captureStackTrace&&Error.captureStackTrace(t,e),t}return t}(),s=(0,i.T)(t);(0,f.e)(()=>a.register(o),[o,a.register]);let c={ref:s,...a.props,id:o};return(0,d.sY)({ourProps:c,theirProps:l,slot:a.slot||{},defaultTag:"p",name:a.name||"Description"})}),{});var m=n(7409);let h=(0,r.createContext)(null),g=Object.assign((0,d.yV)(function(e,t){let n=(0,u.M)(),{id:o="headlessui-label-".concat(n),passive:l=!1,...a}=e,s=function e(){let t=(0,r.useContext)(h);if(null===t){let t=Error("You used a <Label /> component, but it is not inside a relevant parent.");throw Error.captureStackTrace&&Error.captureStackTrace(t,e),t}return t}(),c=(0,i.T)(t);(0,f.e)(()=>s.register(o),[o,s.register]);let p={ref:c,...s.props,id:o};return l&&("onClick"in p&&(delete p.htmlFor,delete p.onClick),"onClick"in a&&delete a.onClick),(0,d.sY)({ourProps:p,theirProps:a,slot:s.slot||{},defaultTag:"label",name:s.name||"Label"})}),{}),y=(0,r.createContext)(null);y.displayName="GroupContext";let b=r.Fragment,E=Object.assign((0,d.yV)(function(e,t){var n;let f=(0,u.M)(),{id:p="headlessui-switch-".concat(f),checked:v,defaultChecked:h=!1,onChange:g,disabled:b=!1,name:E,value:P,form:S,...w}=e,T=(0,r.useContext)(y),N=(0,r.useRef)(null),O=(0,i.T)(N,t,null===T?null:T.setSwitch),[A,C]=function(e,t,n){let[l,u]=(0,r.useState)(n),a=void 0!==e,i=(0,r.useRef)(a),s=(0,r.useRef)(!1),c=(0,r.useRef)(!1);return!a||i.current||s.current?a||!i.current||c.current||(c.current=!0,i.current=a,console.error("A component is changing from controlled to uncontrolled. This may be caused by the value changing from a defined value to undefined, which should not happen.")):(s.current=!0,i.current=a,console.error("A component is changing from uncontrolled to controlled. This may be caused by the value changing from undefined to a defined value, which should not happen.")),[a?e:l,(0,o.z)(e=>(a||u(e),null==t?void 0:t(e)))]}(v,g,h),x=(0,o.z)(()=>null==C?void 0:C(!A)),M=(0,o.z)(e=>{if((0,c.P)(e.currentTarget))return e.preventDefault();e.preventDefault(),x()}),I=(0,o.z)(e=>{e.key===m.R.Space?(e.preventDefault(),x()):e.key===m.R.Enter&&function(e){var t,n;let r=null!=(t=null==e?void 0:e.form)?t:e.closest("form");if(r){for(let t of r.elements)if(t!==e&&("INPUT"===t.tagName&&"submit"===t.type||"BUTTON"===t.tagName&&"submit"===t.type||"INPUT"===t.nodeName&&"image"===t.type)){t.click();return}null==(n=r.requestSubmit)||n.call(r)}}(e.currentTarget)}),k=(0,o.z)(e=>e.preventDefault()),F=(0,r.useMemo)(()=>({checked:A}),[A]),R={id:p,ref:O,role:"switch",type:(0,a.f)(e,N),tabIndex:-1===e.tabIndex?0:null!=(n=e.tabIndex)?n:0,"aria-checked":A,"aria-labelledby":null==T?void 0:T.labelledby,"aria-describedby":null==T?void 0:T.describedby,disabled:b,onClick:M,onKeyUp:I,onKeyPress:k},L=function(){let[e]=(0,r.useState)(function e(){let t=[],n={addEventListener:(e,t,r,o)=>(e.addEventListener(t,r,o),n.add(()=>e.removeEventListener(t,r,o))),requestAnimationFrame(){for(var e=arguments.length,t=Array(e),r=0;r<e;r++)t[r]=arguments[r];let o=requestAnimationFrame(...t);return n.add(()=>cancelAnimationFrame(o))},nextFrame(){for(var e=arguments.length,t=Array(e),r=0;r<e;r++)t[r]=arguments[r];return n.requestAnimationFrame(()=>n.requestAnimationFrame(...t))},setTimeout(){for(var e=arguments.length,t=Array(e),r=0;r<e;r++)t[r]=arguments[r];let o=setTimeout(...t);return n.add(()=>clearTimeout(o))},microTask(){for(var e=arguments.length,t=Array(e),r=0;r<e;r++)t[r]=arguments[r];let o={current:!0};return(0,l.Y)(()=>{o.current&&t[0]()}),n.add(()=>{o.current=!1})},style(e,t,n){let r=e.style.getPropertyValue(t);return Object.assign(e.style,{[t]:n}),this.add(()=>{Object.assign(e.style,{[t]:r})})},group(t){let n=e();return t(n),this.add(()=>n.dispose())},add:e=>(t.push(e),()=>{let n=t.indexOf(e);if(n>=0)for(let e of t.splice(n,1))e()}),dispose(){for(let e of t.splice(0))e()}};return n});return(0,r.useEffect)(()=>()=>e.dispose(),[e]),e}();return(0,r.useEffect)(()=>{var e;let t=null==(e=N.current)?void 0:e.closest("form");t&&void 0!==h&&L.addEventListener(t,"reset",()=>{C(h)})},[N,C]),r.createElement(r.Fragment,null,null!=E&&A&&r.createElement(s._,{features:s.A.Hidden,...(0,d.oA)({as:"input",type:"checkbox",hidden:!0,readOnly:!0,disabled:b,form:S,checked:A,name:E,value:P})}),(0,d.sY)({ourProps:R,theirProps:w,slot:F,defaultTag:"button",name:"Switch"}))}),{Group:function(e){var t;let[n,l]=(0,r.useState)(null),[u,a]=function(){let[e,t]=(0,r.useState)([]);return[e.length>0?e.join(" "):void 0,(0,r.useMemo)(()=>function(e){let n=(0,o.z)(e=>(t(t=>[...t,e]),()=>t(t=>{let n=t.slice(),r=n.indexOf(e);return -1!==r&&n.splice(r,1),n}))),l=(0,r.useMemo)(()=>({register:n,slot:e.slot,name:e.name,props:e.props}),[n,e.slot,e.name,e.props]);return r.createElement(h.Provider,{value:l},e.children)},[t])]}(),[i,s]=function(){let[e,t]=(0,r.useState)([]);return[e.length>0?e.join(" "):void 0,(0,r.useMemo)(()=>function(e){let n=(0,o.z)(e=>(t(t=>[...t,e]),()=>t(t=>{let n=t.slice(),r=n.indexOf(e);return -1!==r&&n.splice(r,1),n}))),l=(0,r.useMemo)(()=>({register:n,slot:e.slot,name:e.name,props:e.props}),[n,e.slot,e.name,e.props]);return r.createElement(p.Provider,{value:l},e.children)},[t])]}(),c=(0,r.useMemo)(()=>({switch:n,setSwitch:l,labelledby:u,describedby:i}),[n,l,u,i]);return r.createElement(s,{name:"Switch.Description"},r.createElement(a,{name:"Switch.Label",props:{htmlFor:null==(t=c.switch)?void 0:t.id,onClick(e){n&&("LABEL"===e.currentTarget.tagName&&e.preventDefault(),n.click(),n.focus({preventScroll:!0}))}}},r.createElement(y.Provider,{value:c},(0,d.sY)({ourProps:{},theirProps:e,defaultTag:b,name:"Switch.Group"}))))},Label:g,Description:v})},641:function(e,t,n){n.d(t,{z:function(){return l}});var r=n(4090),o=n(5235);let l=function(e){let t=(0,o.E)(e);return r.useCallback(function(){for(var e=arguments.length,n=Array(e),r=0;r<e;r++)n[r]=arguments[r];return t.current(...n)},[t])}},1313:function(e,t,n){n.d(t,{M:function(){return i}});var r,o=n(4090),l=n(1879),u=n(9790),a=n(2144);let i=null!=(r=o.useId)?r:function(){let e=(0,a.H)(),[t,n]=o.useState(e?()=>l.O.nextId():null);return(0,u.e)(()=>{null===t&&n(l.O.nextId())},[t]),null!=t?""+t:void 0}},9790:function(e,t,n){n.d(t,{e:function(){return l}});var r=n(4090),o=n(1879);let l=(e,t)=>{o.O.isServer?(0,r.useEffect)(e,t):(0,r.useLayoutEffect)(e,t)}},5235:function(e,t,n){n.d(t,{E:function(){return l}});var r=n(4090),o=n(9790);function l(e){let t=(0,r.useRef)(e);return(0,o.e)(()=>{t.current=e},[e]),t}},1454:function(e,t,n){n.d(t,{f:function(){return u}});var r=n(4090),o=n(9790);function l(e){var t;if(e.type)return e.type;let n=null!=(t=e.as)?t:"button";if("string"==typeof n&&"button"===n.toLowerCase())return"button"}function u(e,t){let[n,u]=(0,r.useState)(()=>l(e));return(0,o.e)(()=>{u(l(e))},[e.type,e.as]),(0,o.e)(()=>{n||t.current&&t.current instanceof HTMLButtonElement&&!t.current.hasAttribute("type")&&u("button")},[n,t]),n}},2144:function(e,t,n){n.d(t,{H:function(){return u}});var r,o=n(4090),l=n(1879);function u(){let e;let t=(e="undefined"==typeof document,(0,(r||(r=n.t(o,2))).useSyncExternalStore)(()=>()=>{},()=>!1,()=>!e)),[u,a]=o.useState(l.O.isHandoffComplete);return u&&!1===l.O.isHandoffComplete&&a(!1),o.useEffect(()=>{!0!==u&&a(!0)},[u]),o.useEffect(()=>l.O.handoff(),[]),!t&&u}},6601:function(e,t,n){n.d(t,{T:function(){return a},h:function(){return u}});var r=n(4090),o=n(641);let l=Symbol();function u(e){let t=!(arguments.length>1)||void 0===arguments[1]||arguments[1];return Object.assign(e,{[l]:t})}function a(){for(var e=arguments.length,t=Array(e),n=0;n<e;n++)t[n]=arguments[n];let u=(0,r.useRef)(t);(0,r.useEffect)(()=>{u.current=t},[t]);let a=(0,o.z)(e=>{for(let t of u.current)null!=t&&("function"==typeof t?t(e):t.current=e)});return t.every(e=>null==e||(null==e?void 0:e[l]))?void 0:a}},7700:function(e,t,n){n.d(t,{A:function(){return l},_:function(){return u}});var r,o=n(7306),l=((r=l||{})[r.None=1]="None",r[r.Focusable=2]="Focusable",r[r.Hidden=4]="Hidden",r);let u=(0,o.yV)(function(e,t){var n;let{features:r=1,...l}=e,u={ref:t,"aria-hidden":(2&r)==2||(null!=(n=l["aria-hidden"])?n:void 0),hidden:(4&r)==4||void 0,style:{position:"fixed",top:1,left:1,width:1,height:0,padding:0,margin:-1,overflow:"hidden",clip:"rect(0, 0, 0, 0)",whiteSpace:"nowrap",borderWidth:"0",...(4&r)==4&&(2&r)!=2&&{display:"none"}}};return(0,o.sY)({ourProps:u,theirProps:l,slot:{},defaultTag:"div",name:"Hidden"})})},4152:function(e,t,n){function r(e){let t=e.parentElement,n=null;for(;t&&!(t instanceof HTMLFieldSetElement);)t instanceof HTMLLegendElement&&(n=t),t=t.parentElement;let r=(null==t?void 0:t.getAttribute("disabled"))==="";return!(r&&function(e){if(!e)return!1;let t=e.previousElementSibling;for(;null!==t;){if(t instanceof HTMLLegendElement)return!1;t=t.previousElementSibling}return!0}(n))&&r}n.d(t,{P:function(){return r}})},1879:function(e,t,n){n.d(t,{O:function(){return a}});var r=Object.defineProperty,o=(e,t,n)=>t in e?r(e,t,{enumerable:!0,configurable:!0,writable:!0,value:n}):e[t]=n,l=(e,t,n)=>(o(e,"symbol"!=typeof t?t+"":t,n),n);class u{set(e){this.current!==e&&(this.handoffState="pending",this.currentId=0,this.current=e)}reset(){this.set(this.detect())}nextId(){return++this.currentId}get isServer(){return"server"===this.current}get isClient(){return"client"===this.current}detect(){return"undefined"==typeof document?"server":"client"}handoff(){"pending"===this.handoffState&&(this.handoffState="complete")}get isHandoffComplete(){return"complete"===this.handoffState}constructor(){l(this,"current",this.detect()),l(this,"handoffState","pending"),l(this,"currentId",0)}}let a=new u},2640:function(e,t,n){n.d(t,{E:function(){return r}});function r(e,t){for(var n=arguments.length,o=Array(n>2?n-2:0),l=2;l<n;l++)o[l-2]=arguments[l];if(e in t){let n=t[e];return"function"==typeof n?n(...o):n}let u=Error('Tried to handle "'.concat(e,'" but there is no handler defined. Only defined handlers are: ').concat(Object.keys(t).map(e=>'"'.concat(e,'"')).join(", "),"."));throw Error.captureStackTrace&&Error.captureStackTrace(u,r),u}},1210:function(e,t,n){n.d(t,{Y:function(){return r}});function r(e){"function"==typeof queueMicrotask?queueMicrotask(e):Promise.resolve().then(e).catch(e=>setTimeout(()=>{throw e}))}},7306:function(e,t,n){n.d(t,{AN:function(){return i},oA:function(){return h},yV:function(){return m},sY:function(){return c},Y2:function(){return f}});var r,o,l=n(4090);function u(){for(var e=arguments.length,t=Array(e),n=0;n<e;n++)t[n]=arguments[n];return Array.from(new Set(t.flatMap(e=>"string"==typeof e?e.split(" "):[]))).filter(Boolean).join(" ")}var a=n(2640),i=((r=i||{})[r.None=0]="None",r[r.RenderStrategy=1]="RenderStrategy",r[r.Static=2]="Static",r),s=((o=s||{})[o.Unmount=0]="Unmount",o[o.Hidden=1]="Hidden",o);function c(e){let{ourProps:t,theirProps:n,slot:r,defaultTag:o,features:l,visible:u=!0,name:i,mergeRefs:s}=e;s=null!=s?s:p;let c=v(n,t);if(u)return d(c,r,o,i,s);let f=null!=l?l:0;if(2&f){let{static:e=!1,...t}=c;if(e)return d(t,r,o,i,s)}if(1&f){let{unmount:e=!0,...t}=c;return(0,a.E)(e?0:1,{0:()=>null,1:()=>d({...t,hidden:!0,style:{display:"none"}},r,o,i,s)})}return d(c,r,o,i,s)}function d(e){let t=arguments.length>1&&void 0!==arguments[1]?arguments[1]:{},n=arguments.length>2?arguments[2]:void 0,r=arguments.length>3?arguments[3]:void 0,o=arguments.length>4?arguments[4]:void 0,{as:a=n,children:i,refName:s="ref",...c}=g(e,["unmount","static"]),d=void 0!==e.ref?{[s]:e.ref}:{},f="function"==typeof i?i(t):i;"className"in c&&c.className&&"function"==typeof c.className&&(c.className=c.className(t));let p={};if(t){let e=!1,n=[];for(let[r,o]of Object.entries(t))"boolean"==typeof o&&(e=!0),!0===o&&n.push(r);e&&(p["data-headlessui-state"]=n.join(" "))}if(a===l.Fragment&&Object.keys(h(c)).length>0){if(!(0,l.isValidElement)(f)||Array.isArray(f)&&f.length>1)throw Error(['Passing props on "Fragment"!',"","The current component <".concat(r,' /> is rendering a "Fragment".'),"However we need to passthrough the following props:",Object.keys(c).map(e=>"  - ".concat(e)).join("\n"),"","You can apply a few solutions:",['Add an `as="..."` prop, to ensure that we render an actual element instead of a "Fragment".',"Render a single element as the child so that we can forward the props onto that element."].map(e=>"  - ".concat(e)).join("\n")].join("\n"));let e=f.props,t="function"==typeof(null==e?void 0:e.className)?function(){for(var t=arguments.length,n=Array(t),r=0;r<t;r++)n[r]=arguments[r];return u(null==e?void 0:e.className(...n),c.className)}:u(null==e?void 0:e.className,c.className);return(0,l.cloneElement)(f,Object.assign({},v(f.props,h(g(c,["ref"]))),p,d,{ref:o(f.ref,d.ref)},t?{className:t}:{}))}return(0,l.createElement)(a,Object.assign({},g(c,["ref"]),a!==l.Fragment&&d,a!==l.Fragment&&p),f)}function f(){let e=(0,l.useRef)([]),t=(0,l.useCallback)(t=>{for(let n of e.current)null!=n&&("function"==typeof n?n(t):n.current=t)},[]);return function(){for(var n=arguments.length,r=Array(n),o=0;o<n;o++)r[o]=arguments[o];if(!r.every(e=>null==e))return e.current=r,t}}function p(){for(var e=arguments.length,t=Array(e),n=0;n<e;n++)t[n]=arguments[n];return t.every(e=>null==e)?void 0:e=>{for(let n of t)null!=n&&("function"==typeof n?n(e):n.current=e)}}function v(){for(var e=arguments.length,t=Array(e),n=0;n<e;n++)t[n]=arguments[n];if(0===t.length)return{};if(1===t.length)return t[0];let r={},o={};for(let e of t)for(let t in e)t.startsWith("on")&&"function"==typeof e[t]?(null!=o[t]||(o[t]=[]),o[t].push(e[t])):r[t]=e[t];if(r.disabled||r["aria-disabled"])return Object.assign(r,Object.fromEntries(Object.keys(o).map(e=>[e,void 0])));for(let e in o)Object.assign(r,{[e](t){for(var n=arguments.length,r=Array(n>1?n-1:0),l=1;l<n;l++)r[l-1]=arguments[l];for(let n of o[e]){if((t instanceof Event||(null==t?void 0:t.nativeEvent)instanceof Event)&&t.defaultPrevented)return;n(t,...r)}}});return r}function m(e){var t;return Object.assign((0,l.forwardRef)(e),{displayName:null!=(t=e.displayName)?t:e.name})}function h(e){let t=Object.assign({},e);for(let e in t)void 0===t[e]&&delete t[e];return t}function g(e){let t=arguments.length>1&&void 0!==arguments[1]?arguments[1]:[],n=Object.assign({},e);for(let e of t)e in n&&delete n[e];return n}}}]);