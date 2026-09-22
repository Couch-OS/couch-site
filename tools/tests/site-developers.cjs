// Check the generated developer knowledge base at desktop and phone widths.
const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const path=require('node:path');
const os=require('node:os');
const {execFileSync}=require('node:child_process');

const base=process.env.SITE_URL||'http://127.0.0.1:8098/';
const couchSource=process.env.COUCH_SOURCE&&path.resolve(process.env.COUCH_SOURCE);
const pages=['','getting-started.html','protocol.html','components.html','packaging.html','testing.html','admission.html'];
const minimumCodeBlocks={'':1,'getting-started.html':4,'protocol.html':5,'components.html':1,'packaging.html':4,'testing.html':2,'admission.html':1};

(async()=>{
 const browser=await chromium.launch();
 const errors=[];
 try {
  const page=await browser.newPage();
  page.on('pageerror',error=>errors.push(error.message));
  const badResponses=[];
  page.on('response',response=>{if(response.status()>=400)badResponses.push(`${response.status()} ${response.url()}`)});
  const sourceCommits=new Set();
  for(const slug of pages){
   for(const width of [1440,390,320]){
    await page.setViewportSize({width,height:1000});
    await page.goto(new URL(`developers/${slug}`,base).href);
    assert.equal(await page.locator('main').count(),1,`${slug} has one main landmark`);
    assert.equal(await page.locator('h1').count(),1,`${slug} has one h1`);
    assert.ok(await page.locator('h2').count()>=3,`${slug} has useful section headings`);
    assert.ok(await page.locator('pre code').count()>=minimumCodeBlocks[slug],`${slug} retains its code examples`);
    assert.equal(await page.getByRole('navigation',{name:'Main navigation'}).count(),1);
    assert.equal(await page.getByRole('navigation',{name:'Developer topics'}).count(),1);
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,`${slug} overflows at ${width}`);
    const ids=await page.locator('[id]').evaluateAll(nodes=>nodes.map(node=>node.id));
    assert.equal(new Set(ids).size,ids.length,`${slug} has unique IDs`);
    const source=await page.getByRole('link',{name:'View Markdown'}).getAttribute('href');
    const edit=await page.getByRole('link',{name:'Suggest an edit'}).getAttribute('href');
    const sourceMatch=source.match(/\/blob\/([0-9a-f]{40})\/docs\/development\//);
    const editMatch=edit.match(/\/edit\/([0-9a-f]{40})\/docs\/development\//);
    assert.ok(sourceMatch,`${slug} source link is pinned`);
    assert.equal(editMatch?.[1],sourceMatch[1],`${slug} edit link uses the source commit`);
    sourceCommits.add(sourceMatch[1]);
    assert.equal(await page.locator('a[href*="/blob/main/"], a[href*="/tree/main/"]').count(),0,`${slug} has no moving source links`);
   }
  }
  assert.equal(sourceCommits.size,1,'all pages come from one Couch commit');
  if(couchSource){
   const expected=execFileSync('git',['rev-parse','HEAD'],{cwd:couchSource,encoding:'utf8'}).trim();
   assert.deepEqual([...sourceCommits],[expected],'documentation links use the rendered Couch checkout');
  }

  await page.setViewportSize({width:1440,height:1000});
  await page.goto(new URL('developers/',base).href);
  const cards=page.locator('.developer-card');
  const topics=await cards.count();
  assert.equal(topics,7,'index exposes every topic');
  const search=page.getByRole('searchbox',{name:'Find a topic'});
  await search.fill('chroot');
  assert.equal(await page.locator('.developer-card:visible').count(),1,'search narrows topics');
  assert.match(await page.locator('[data-search-status]').textContent(),/1 topic found/);
  await search.fill('pairing events');
  assert.ok(await page.locator('.developer-card:visible').count()>=1,'search includes guide content and combines words');
  await search.fill('');
  assert.equal(await page.locator('.developer-card:visible').count(),topics,'clearing the search shows every topic again');

  const checked=new Set();
  for(const slug of pages){
   await page.goto(new URL(`developers/${slug}`,base).href);
   for(const href of await page.locator('a[href]').evaluateAll(links=>links.map(link=>link.href))){
    const url=new URL(href);
    if(url.origin!==new URL(base).origin)continue;
    if(url.hash){
     const documentUrl=new URL(url);documentUrl.hash='';
     const current=new URL(page.url());current.hash='';
     if(documentUrl.href===current.href){
      const fragment=decodeURIComponent(url.hash.slice(1));
      assert.equal(await page.evaluate(id=>Boolean(document.getElementById(id)),fragment),true,`broken heading link ${href}`);
      continue;
     }
    }
    const requestUrl=new URL(url);requestUrl.hash='';
    if(checked.has(requestUrl.href))continue;
    checked.add(requestUrl.href);
    const response=await page.request.get(requestUrl.href);
    assert.ok(response.ok(),`broken local link ${requestUrl.href}`);
   }
  }

  await page.setViewportSize({width:1440,height:1000});
  await page.goto(new URL('developers/',base).href);
  await page.screenshot({path:path.join(os.tmpdir(),'couch-developers-desktop.png'),fullPage:true});
  await page.setViewportSize({width:390,height:844});
  await page.goto(new URL('developers/protocol.html',base).href);
  await page.screenshot({path:path.join(os.tmpdir(),'couch-developers-mobile.png'),fullPage:true});
  assert.deepEqual(errors,[]);
  assert.deepEqual(badResponses,[]);
  console.log('PASS: seven developer pages, responsive layouts, search, landmarks, pinned source/edit links, headings and local links.');
 } finally {await browser.close();}
})().catch(error=>{console.error(error);process.exit(1)});
