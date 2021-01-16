# Backend Projects


- [Simple OCR Letters](https://github.com/teletraan/takehome/blob/master/backend/simple_ocr_letters.md)

## 识别图片中的字母

- POST: /api/ocr/upload
- params:

| 参数名 | 类型  | 是否必须 | 默认值 | 含义   |
| :----- | ----- | -------- | ------ | ------ |
| id     | int   | 是       |        | 用户id |
| file   | image | 是       |        | 图片   |

- return:

```json
{
  code: 200,
  letters: "abcde"
}
```

## 获取id对应的全部识别记录

- GET: /api/ocr/records
- params:

| 参数名   | 类型 | 是否必须 | 默认值 | 含义     |
| :------- | ---- | -------- | ------ | -------- |
| id       | int  | 是       |        | 用户id   |
| page     | Int  | 否       |        | 页码     |
| pageSize | int  | 否       |        | 每页大小 |

- return:

```json
{
  code: 200,
  data: [
	{
            "id": 8,
            "userId": "2",
            "letters": null,
            "createTime": "2021-01-15 00:10:22",
            "updateTime": "2021-01-15 00:10:22"
        },
  ]
}
```

## 注册

- POST: /api/ocr/register
- params:

| 参数名   | 类型   | 是否必须 | 默认值 | 含义   |
| :------- | ------ | -------- | ------ | ------ |
| username | string | 是       |        | 用户名 |
| password | String | 是       |        | 图密码 |

- return:

```json
{
  code: 200,
  "user": {
      "username": "dkkk",
      "createTime": ""
  }
}
```

## 