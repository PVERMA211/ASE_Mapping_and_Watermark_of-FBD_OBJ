# ASE_Mapping_and_Watermark_of-FBD_OBJ

Deploy n8n on a machine with Docker Compose and validate the local runtime prerequisites before starting it.

## Requirements

- Docker Engine
- Docker Compose v2
- Python 3.14 on the host machine

## Files

- `/tmp/workspace/PVERMA211/ASE_Mapping_and_Watermark_of-FBD_OBJ/docker-compose.yml` - n8n deployment
- `/tmp/workspace/PVERMA211/ASE_Mapping_and_Watermark_of-FBD_OBJ/.env.example` - default environment values
- `/tmp/workspace/PVERMA211/ASE_Mapping_and_Watermark_of-FBD_OBJ/scripts/validate_requirements.py` - prerequisite validator
- `/tmp/workspace/PVERMA211/ASE_Mapping_and_Watermark_of-FBD_OBJ/scripts/deploy_n8n.sh` - deployment entrypoint
- `/tmp/workspace/PVERMA211/ASE_Mapping_and_Watermark_of-FBD_OBJ/scripts/smoke_test_n8n.sh` - post-start validation

## Setup

1. Copy `.env.example` to `.env`.
2. Install Python 3.14 and make `python3.14` available on the machine.
3. Run:

   ```bash
   /tmp/workspace/PVERMA211/ASE_Mapping_and_Watermark_of-FBD_OBJ/scripts/deploy_n8n.sh
   ```

## Validation

Run the prerequisite validator directly:

```bash
python3.14 /tmp/workspace/PVERMA211/ASE_Mapping_and_Watermark_of-FBD_OBJ/scripts/validate_requirements.py --project-root /tmp/workspace/PVERMA211/ASE_Mapping_and_Watermark_of-FBD_OBJ
```

Run the smoke test after deployment:

```bash
/tmp/workspace/PVERMA211/ASE_Mapping_and_Watermark_of-FBD_OBJ/scripts/smoke_test_n8n.sh
```