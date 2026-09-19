# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: complete-lifecycle.spec.ts >> Complete Product Lifecycle - Strict >> should complete full upgrade lifecycle with strict assertions
- Location: tests\e2e\complete-lifecycle.spec.ts:34:7

# Error details

```
Error: expect(locator).toContainText(expected) failed

Locator: locator('h1')
Expected substring: "项目导入"
Received string:    "Welcome to Grafana"
Timeout: 5000ms

Call log:
  - Expect "toContainText" locator('h1') with timeout 5000ms
  - waiting for locator('h1')
    10 × locator resolved to <h1 class="css-1gmqqtf">Welcome to Grafana</h1>
       - unexpected value "Welcome to Grafana"

```

```yaml
- heading "Welcome to Grafana" [level=1]
```

# Test source

```ts
  1   | /**
  2   |  * Playwright E2E Test: Complete Product Lifecycle with Strict Assertions
  3   |  * 
  4   |  * Tests the full upgrade lifecycle with REAL assertions:
  5   |  * Import → Audit → Plan → Task → Execute → VERIFY → Evidence → Version → Interview → Answer → Assessment
  6   |  * 
  7   |  * Strict requirements:
  8   |  * - Execute must call Verify EXPLICITLY (execute does NOT auto-verify)
  9   |  * - verification_id must exist after verify
  10  |  * - evidence.length > 0
  11  |  * - versions.length > 0
  12  |  * - No "暂无证据" allowed to pass
  13  |  * - Interview must submit real answer
  14  |  * - Assessment must exist
  15  |  * - Weak answer should trigger follow-up
  16  |  */
  17  | 
  18  | import { test, expect } from '@playwright/test';
  19  | 
  20  | // Configuration
  21  | const FRONTEND_URL = 'http://localhost:3000'
  22  | const API_BASE = 'http://localhost:8000'
  23  | 
  24  | // Use a test GitHub URL (public repo)
  25  | const TEST_GITHUB_URL = 'https://github.com/Benjamindaoson/AIEduRAG'
  26  | const WEAK_ANSWER = '我不知道，可能是因为代码有问题吧。' // Weak answer to trigger follow-up
  27  | 
  28  | test.describe('Complete Product Lifecycle - Strict', () => {
  29  |   let projectId: string | null = null
  30  |   let taskId: string | null = null
  31  |   let executionId: string | null = null
  32  |   let verificationId: string | null = null
  33  | 
  34  |   test('should complete full upgrade lifecycle with strict assertions', async ({ page }) => {
  35  |     // Step 1: Import project
  36  |     await page.goto(`${FRONTEND_URL}/projects/import`)
> 37  |     await expect(page.locator('h1')).toContainText('项目导入')
      |                                      ^ Error: expect(locator).toContainText(expected) failed
  38  |     
  39  |     // Enter GitHub URL
  40  |     await page.fill('input[placeholder*="github.com"]', TEST_GITHUB_URL)
  41  |     
  42  |     // Click import button
  43  |     await page.click('button:has-text("开始导入")')
  44  |     
  45  |     // Wait for import to complete
  46  |     await expect(page.locator('text=导入成功')).toBeVisible({ timeout: 120000 })
  47  |     
  48  |     // Extract project ID from the import result
  49  |     const projectIdElement = page.locator('code').first()
  50  |     await expect(projectIdElement).toBeVisible()
  51  |     projectId = await projectIdElement.textContent()
  52  |     console.log('Project ID:', projectId)
  53  |     
  54  |     // Step 2: Audit project
  55  |     await page.goto(`${FRONTEND_URL}/projects/health?project_id=${projectId}`)
  56  |     await expect(page.locator('h1')).toContainText('项目体检')
  57  |     
  58  |     // Click audit button
  59  |     await page.click('button:has-text("开始体检"), button:has-text("重新体检")')
  60  |     
  61  |     // Wait for audit to complete
  62  |     await expect(page.locator('text=当前阶段')).toBeVisible({ timeout: 120000 })
  63  |     
  64  |     // Verify maturity assessment is shown
  65  |     await expect(page.locator('text=整体成熟度')).toBeVisible()
  66  |     
  67  |     // Step 3: Plan upgrades
  68  |     await page.goto(`${FRONTEND_URL}/upgrade-map?project_id=${projectId}`)
  69  |     await expect(page.locator('h1')).toContainText('升级地图')
  70  |     
  71  |     // Generate plan (if not already generated)
  72  |     const generateButton = page.locator('button:has-text("生成升级计划")')
  73  |     if (await generateButton.isVisible()) {
  74  |       await generateButton.click()
  75  |       await expect(page.locator('text=推荐升级任务')).toBeVisible({ timeout: 60000 })
  76  |     }
  77  |     
  78  |     // Verify recommended tasks are shown
  79  |     await expect(page.locator('text=推荐升级任务')).toBeVisible()
  80  |     
  81  |     // Step 4: Select a task
  82  |     const taskLink = page.locator('a:has-text("开始任务")').first()
  83  |     await taskLink.click()
  84  |     await expect(page.locator('h1')).toContainText('工程任务')
  85  |     
  86  |     // Extract task ID from URL
  87  |     const url = page.url()
  88  |     const urlParams = new URL(url)
  89  |     taskId = urlParams.searchParams.get('task_id')
  90  |     console.log('Task ID:', taskId)
  91  |     
  92  |     // Step 5: Execute task via API directly to get execution_id
  93  |     if (taskId) {
  94  |       const executeResponse = await page.request.post(`${API_BASE}/api/tasks/${taskId}/execute`)
  95  |       expect(executeResponse.ok()).toBeTruthy()
  96  |       const executeResult = await executeResponse.json()
  97  |       
  98  |       // Get execution_id from execute result
  99  |       executionId = executeResult.execution_id
  100 |       console.log('Execution ID:', executionId)
  101 |       
  102 |       // Execution should complete
  103 |       expect(executeResult.status === 'completed' || executeResult.status === 'failed').toBe(true)
  104 |     }
  105 |     
  106 |     // Step 6: VERIFY - MUST call explicitly after execute (execute does NOT auto-verify)
  107 |     expect(executionId).toBeDefined()
  108 |     console.log('Calling verify for execution:', executionId)
  109 |     
  110 |     const verifyResponse = await page.request.post(`${API_BASE}/api/executions/${executionId}/verify`)
  111 |     expect(verifyResponse.ok()).toBeTruthy()
  112 |     const verifyResult = await verifyResponse.json()
  113 |     
  114 |     // Verify result must have verification_id
  115 |     verificationId = verifyResult.verification_id
  116 |     expect(verificationId).toBeDefined()
  117 |     console.log('Verification ID:', verificationId)
  118 |     
  119 |     // Verify result must have evidence_ids
  120 |     expect(verifyResult.evidence_ids).toBeDefined()
  121 |     expect(Array.isArray(verifyResult.evidence_ids)).toBe(true)
  122 |     console.log('Evidence IDs:', verifyResult.evidence_ids)
  123 |     
  124 |     // Step 7: View Evidence and verify it exists
  125 |     await page.goto(`${FRONTEND_URL}/evidence?project_id=${projectId}`)
  126 |     await expect(page.locator('h1')).toContainText('证据')
  127 |     
  128 |     // Wait for evidence to load
  129 |     await page.waitForTimeout(2000)
  130 |     
  131 |     // STRICT: Must have evidence - "暂无证据" is NOT allowed
  132 |     const noEvidenceText = page.locator('text=暂无证据')
  133 |     const hasNoEvidence = await noEvidenceText.isVisible().catch(() => false)
  134 |     expect(hasNoEvidence).toBe(false)
  135 |     
  136 |     // Check evidence via API to confirm
  137 |     const evidenceResponse = await page.request.get(`${API_BASE}/api/projects/${projectId}/evidence`)
```