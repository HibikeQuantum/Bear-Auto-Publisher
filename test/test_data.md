# test ??
//헤드는 문법이 동일하다. 바꾸지 않아도 된다.

라인세퍼레이터
---
//세퍼레이터는 개행---으로 바꿔준다. 깃허브에선 세퍼라인 위쪽 글자가 두꺼워져보이는데, 불필요하다.

*볼드체*
//* *은 **볼드체** 로 바꿔주고

/이텔릭/
//    /이태릭/은 *이태릭* 으로 바꿔주고

_언더라인_
//"언더라인은 ***언더라인*** 으로 바꿔주고

-스트라이크-
//"스트라이크는 ~~이렇게~~

* 불릿
	* 불릿2
		* 불릿3
		* 불릿3-1
//불릿은 \t * 으로 바꿔준다

1. 오더1
	1. 오더2
		1. 오더3

> 쿼트.. 이것이 인생
// 라이트 앵글 브라켓은 안바꿔줘도 된다.

Check Box
- 투두
+ 투두완료
- [ ]
// -tab은 체크박스를
- [x]
// +tab은 컴플릿 체크박스를 표현하도록 바꿔준다. ^-\t 다.

code highlight
`var a = 10;`
// 바꿀 필요 없다.

```json
{
  "cleanOutputDir": true,
  "exportTrash": false,
  "exportImages": true,
  "exportFiles": true,
  "outputDir": "~/OneDrive/Bear Notes"
}
```

마크드 스트링 (폰트 배경색)
::marked String::
```diff
+ marked String
```
// 깃헙에서 지원을 안한다. 하지만 유용한것 같으니
// 그냥 이렇게 강제 개행시키고 기능을 지원하는게 좋겠다.

file 링크
[file:5C01D883-4077-4954-8E28-B7C91ED285B7-67965-000005BA6002A679/myimsi.txt]
이런 패턴을 보면
[?myimsi.txt](https://github.com/HibikeQuantum/PlayGround/blob/master/Bear/files/5C01D883-4077-4954-8E28-B7C91ED285B7-67965-000005BA6002A679/myimsi.txt)
이렇게 바꿔준다.


image 링크
[image:SFNoteIntro0_File1/Bear 3 columns.png]
이런 텍스트가 보이면 
![alt text](images/SFNoteIntro2_File0/Pro.jpg)
이렇게 바꿔준다.

태그패턴 처리방법 정리
#welcome/Bear
1) #으로부터 한덩이를 자르고 제일 마지막까지 '/'으로 잘라서 nested한 구조로 저장한다.(+예상되는 URL도 쌍으로) 파싱과정에서 notag문서는 여기에 없다.
2) 이제 파싱을 시작한다. 이때는 이걸 만나면 찾아서 URL로 replace하면된다.
3) Navi.md 에선 가장 nested한 구조를 표현해서 링크를 표시한다.
4) 본문에선 아래와 같이 표현
[?welcome/Bear](/Bear/Welcome_to_Bear.md)
4) URL은 부모면 내비게이트 md, 말단 노트 풀패스 md